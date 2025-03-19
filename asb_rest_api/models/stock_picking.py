import base64
import json
import requests
import ast
import logging
import sys
import time

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_invoice_numbers(self):
        for rec in self:
            invoice_number_list = rec.mapped('sale_id').filtered(
                lambda so: so.state != 'cancel' and so.invoice_number).mapped('invoice_number')
            rec.invoice_numbers = ', '.join(invoice_number_list)

    is_need_to_enter_airway_bill = fields.Boolean(string='Is Need Airway Bill',
                                                  related='sale_id.is_need_to_enter_airway_bill', store=True)
    airway_bill = fields.Char(string='Airway Bill', compute='_compute_airway_bill', inverse='_inverse_airway_bill')
    shipping_distance = fields.Float(string='Shipping Distance', related='sale_id.shipping_distance', store=True)
    shipping_note = fields.Text(string='Shipping Note', related='sale_id.shipping_note', store=True)
    shipping_name = fields.Char(
        string='Shipping Name',
        compute=False,
        related=False,
        store=True,
    )
    courier_name = fields.Char(
        string='Courier Name',
    )
    shipping_name_readonly = fields.Char(
        string='Shipping Name API',
        related='shipping_name'
    )
    shipping_service_name = fields.Char(
        string='Delivery Service',
        compute=False,
        related=False,
        store=True,
    )
    shipping_service_name_readonly = fields.Char(
        string='Delivery Service API',
        related='shipping_service_name'
    )
    shipping_price = fields.Float(string='Shipping Price', related='sale_id.shipping_price', store=True)
    shipping_discount = fields.Float(string='Shipping Discount', related='sale_id.shipping_discount', store=True)
    driver_name = fields.Char(string='Driver Name', related='sale_id.driver_name', store=True)
    driver_phone = fields.Char(string='Driver Phone', related='sale_id.driver_phone', store=True)
    driver_photo_url_path = fields.Char(string='Driver Photo Url', related='sale_id.driver_photo_url_path', store=True)
    driver_plate_number = fields.Char(
        string='License Plate',
        compute=False,
        related=False,
        store=True,
    )
    driver_plate_number_readonly = fields.Char(
        string='License Plate API',
        related='driver_plate_number'
    )
    driver_vehicle_model = fields.Char(string='Driver Vehicle Model', related='sale_id.driver_vehicle_model', store=True)
    tracking_url = fields.Char(string='Tracking URL', related='sale_id.tracking_url', store=True)
    carrier_tracking_url = fields.Char(string='Tracking URL Origin')
    delivery_status = fields.Char(string='Delivery Status', related='sale_id.delivery_status', store=True)
    is_from_api = fields.Boolean(string='is from api ?', related='sale_id.is_from_api', store=True)
    recipient_name_web = fields.Char(string='Recipient Name (Web)', related='sale_id.recipient_name_web')
    recipient_phone_web = fields.Char(string='Recipient Phone (Web)', related='sale_id.recipient_phone_web')
    recipient_address_web = fields.Char(string='Recipient Address (Web)', related='sale_id.recipient_address_web')
    invoice_numbers = fields.Char(
        string='Invoice Numbers',
        compute='_get_invoice_numbers')

    @api.depends('airway_bill')
    def _compute_airway_bill(self):
        for picking in self:
            if picking.sale_id.airway_bill:
                picking.airway_bill = picking.sale_id.airway_bill
            else:
                picking.airway_bill = False
    
    def _inverse_airway_bill(self):
        for picking in self:
            if picking.airway_bill:
                picking.sale_id.airway_bill = picking.airway_bill
            else:
                picking.sale_id.airway_bill = False

    def _auto_create_refund_invoice(self, sale_id):
        inv_line_vals = []
        for move_id in self.move_ids_without_package:
            sale_line_id = move_id.sale_line_id
            quantity = move_id.product_uom._compute_quantity(move_id.quantity_done, sale_line_id.product_uom)
            accounts = sale_line_id.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=False)
            inv_line_vals.append((0, 0, {
                'product_id': sale_line_id.product_id.id,
                'name': sale_line_id.product_id.display_name,
                'quantity': quantity,
                'product_uom_id': sale_line_id.product_uom.id,
                'price_unit': sale_line_id.price_unit,
                'account_id': accounts['income'],
                'sale_line_ids': [(6, 0, sale_line_id.ids)]
            }))
        invoice_vals = {
            'partner_id': sale_id.partner_id.id,
            'move_type': 'out_refund',
            'invoice_date': datetime.now(),
            'ref': f'Reversal of: {sale_id.name}',
            'invoice_user_id': sale_id.user_id.id,
            'team_id': sale_id.team_id.id,
            'invoice_line_ids': inv_line_vals
        }
        refund_invoice_id = self.env['account.move'].create(invoice_vals)
        refund_invoice_id.action_post()

    def _action_done(self):
        res = True
        for picking in self:
            wh_pick_id = picking.picking_type_id.warehouse_id.pick_type_id
            if picking.sale_id and picking.sale_id.is_from_api and picking.picking_type_id == wh_pick_id:
                if picking.sale_id.is_need_to_enter_airway_bill and not picking.airway_bill:
                    raise ValidationError(_('Airway Bill must entered for sync to customer in website.'))
                if picking._sync_deliver_order(picking.sale_id, picking.airway_bill):
                    super(StockPicking, picking)._action_done()
            else:
                super(StockPicking, picking)._action_done()
        for picking in self.filtered(lambda p:
                                     p.state == 'done'
                                     and p.location_dest_id.usage == 'customer'
                                     and p.sale_id):
            self.env['sale.order']._auto_create_invoice(picking.sale_id)
        if not self.env.context.get('skip_refund'):
            for picking in self.filtered(lambda p:
                                         p.state == 'done'
                                         and p.location_id.usage == 'customer'
                                         and p.sale_id):
                picking.sudo()._auto_create_refund_invoice(picking.sale_id)
        return res
    
    def _sync_deliver_order(self, sale_order_id, airway_bill):
        # agar tidak kirim 2 kali ke FE
        other_pick_ids = sale_order_id.picking_ids.filtered(lambda p: p.id != self.id and p.location_dest_id.usage != 'customer' and p.state == 'done')
        if other_pick_ids:
            return True
        if sale_order_id.bypass_sync:
            return True
        parameter = "orders_deliver"
        auth = sale_order_id._get_auth()
        url = sale_order_id._get_url_with_id(parameter, sale_order_id.farmaku_order_id)
        headers = {
            "Authorization": "Basic {auth}".format(auth=auth),
            "Content-Type": "application/json"
        }
        body = {
            "airwayBill": airway_bill
        }
        retries = 1
        success = False
        error_message = ''
        response_text = ''
        while not success and retries <= 3:
            try:
                r = requests.put(url=url, headers=headers, json=body)
                response_text = r.text
                success = True
                _logger.info('# Request Obtaining Order Delivery #')
                self.env.user.create_connector_log(
                    url=url,
                    method='PUT',
                    headers=headers,
                    body=body,
                    response=r,
                    response_body=False,
                )
                if r.status_code == 200:
                    _logger.info('# Request Obtaining Order Delivery Success #')
                    _logger.info(r.text)
                elif r.status_code == 404:
                    error_message = '404 not found.'
                else:
                    _logger.warning('# Request Obtaining Deliver Order Failed, code {code} #'.format(
                        code=r.status_code))
                    _logger.warning(r.text)
                    response_data = r.json()
                    detail = response_data.get('detail')
                    farmaku_error_message = detail
                    if isinstance(detail, str):
                        if 'ErrorMessage' in detail:
                            farmaku_error_message = ast.literal_eval(
                                detail.replace('null', '""'))[0]['ErrorMessage']
                    # farmaku_error_message = {"header": {"error_code": "LGS_USC_007"}}
                    if (isinstance(farmaku_error_message, dict)
                            and farmaku_error_message.get('header', {}).get('error_code')
                            and farmaku_error_message.get('header', {}).get('error_code') == 'LGS_USC_007'):
                        pass
                    else:
                        error_message = farmaku_error_message
            except Exception as e:
                wait = 10
                sys.stdout.flush()
                time.sleep(wait)
                retries += 1
                _logger.error(str(e.args[0]))
                self.env.user.create_connector_log(
                    url=url,
                    method='PUT',
                    headers=headers,
                    body=body,
                    response=False,
                    response_body=base64.b64encode(json.dumps({'error': str(e.args[0])}).encode()),
                )
                error_message = str(e.args[0])
        if error_message == 'invalid syntax':
            error_message = response_text
        if error_message:
            self.message_post(body=_(f'Error: {error_message}'))
        return not bool(error_message)

    @api.model
    def _create_move_lines_for_pos_order(self, moves, set_quantity_done_on_move=False):
        res = super(StockPicking, self)._create_move_lines_for_pos_order(moves, set_quantity_done_on_move)
        return res

    def _cron_fill_empty_shipping(self):
        warehouse_ids = self.env['stock.warehouse'].sudo().search([])
        pick_type_ids = warehouse_ids.mapped('pick_type_id')
        pick_ids = self.env['stock.picking'].sudo().search([
            ('state', '=', 'assigned'),
            ('group_id.sale_id', '!=', False),
            '|',
            ('group_id.sale_id.shipping_name', '=', ''),
            ('group_id.sale_id.shipping_name', '=', False),
            ('group_id.sale_id.farmaku_order_id', '!=', False),
            ('group_id.sale_id.team_id.is_pos', '=', False),
            ('picking_type_id', 'in', pick_type_ids.ids),
        ])
        parameter = "orders"
        for pick_id in pick_ids:
            sale_id = pick_id.sale_id
            auth = sale_id._get_auth()
            url = sale_id._get_url_with_id(parameter, sale_id.farmaku_order_id)
            headers = {
                "Authorization": "Basic {auth}".format(auth=auth),
                "Content-Type": "application/json"
            }

            retries = 1
            success = False
            while not success and retries <= 3:
                try:
                    _logger.info(f'\nurl: {url}')
                    r = requests.get(url=url, headers=headers, timeout=5)
                    _logger.info(f'\nresponse: {r.text}')
                    _logger.info(f'\nsale.name: {sale_id.name}')
                    success = True
                    if r.status_code == 200:
                        _logger.info('# Request Obtaining Get Order Info Success #')
                        data = r.json()
                        sale_id.sudo().write({
                            'shipping_note': data['delivery'].get('shippingNote'),
                            'shipping_name': data['delivery'].get(
                                'shippingName') or data['delivery'].get('shippingServiceName'),
                            'shipping_service_name': data['delivery'].get('shippingServiceName'),
                        })
                        pick_id.sudo().write({
                            'shipping_note': data['delivery'].get('shippingNote'),
                            'shipping_name': data['delivery'].get(
                                'shippingName') or data['delivery'].get('shippingServiceName'),
                            'shipping_service_name': data['delivery'].get('shippingServiceName'),
                        })
                except Exception as e:
                    _logger.error(str(e))
