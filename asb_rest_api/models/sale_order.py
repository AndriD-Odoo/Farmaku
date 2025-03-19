import base64
import json
import requests
import pytz
import sys
import time
import ast

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
from datetime import datetime, date
from dateutil import tz
import dateutil.parser
from odoo.addons.ms_rest_api.models.common import (
    _logger,
    success_response,
    error_response,
    authentication,
    check_mandatory_fields
)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    farmaku_order_id = fields.Integer(string='Farmaku Order ID')
    order_number = fields.Char(string='Order Number')
    order_status = fields.Char(string='Order Status')
    invoice_number = fields.Char(string='Invoice Number')
    grand_total_price = fields.Float(string='Grand Total Price')
    has_concoction = fields.Boolean(string='Concoction ?')
    pharmacy_code = fields.Char(string='Pharmacy Code')
    pharmacy_name = fields.Char(string='Pharmacy Name')
    is_need_to_enter_airway_bill = fields.Boolean(string='Is Need Airway Bill', default=False)

    cancel_reason_id = fields.Many2one('cancel.reason', string='Cancel Reason')
    cancel_note = fields.Text(string='Cancel Note')
    airway_bill = fields.Char(string='Airway Bill')
    shipping_distance = fields.Float(string='Shipping Distance')
    shipping_note = fields.Text(string='Shipping Note')
    shipping_name = fields.Char(string='Shipping Name')
    shipping_service_name = fields.Char(string='Delivery Service')
    shipping_price = fields.Float(string='Shipping Price')
    shipping_discount = fields.Float(string='Shipping Discount')

    driver_name = fields.Char(string='Driver Name')
    driver_phone = fields.Char(string='Driver Phone')
    driver_photo_url_path = fields.Char(string='Driver Photo')
    driver_plate_number = fields.Char(string='License Plate')
    driver_vehicle_model = fields.Char(string='Driver Vehicle Model')
    tracking_url = fields.Char(string='Tracking Url')
    delivery_status = fields.Char(string='Delivery Status')

    recipient_name_web = fields.Char(string='Recipient Name (Web)')
    recipient_phone_web = fields.Char(string='Recipient Phone (Web)')
    recipient_address_web = fields.Char(string='Recipient Address (Web)')

    is_from_api = fields.Boolean(string='is from api ?', default=False)
    bypass_sync = fields.Boolean()
    payment_method = fields.Char(
        string='Payment Method',
        required=False)

    def write(self, values):
        res = super(SaleOrder, self).write(values)
        for rec in self:
            if values.get('warehouse_id') and not self.env.context.get('skip_sync_to_fe'):
                rec._sync_change_warehouse(order_id=rec.farmaku_order_id)
        return res

    def compute_refund_status(self):
        res = super(SaleOrder, self).compute_refund_status()
        for rec in self:
            if rec.refund_status == 'full' and not self.env.context.get('skip_sync_to_fe'):
                if not rec.cancel_reason_id and rec.farmaku_order_id:
                    raise ValidationError(_(f'Please input cancel reason for SO {rec.name}.'))
                rec._sync_cancel_order()
        return res

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.invoice_number:
            invoice_vals['ref'] = self.invoice_number
        user_tz = self.env.user.tz or 'Asia/Jakarta'
        if self.date_order:
            invoice_vals['invoice_date'] = pytz.UTC.localize(self.date_order).astimezone(pytz.timezone(user_tz))
        if self.team_id:
            partner_bank_id = self.get_partner_bank_id()
            invoice_vals['partner_bank_id'] = partner_bank_id
        invoice_vals.update({
            'order_number': self.order_number,
            'payment_method': self.payment_method,
            'edc_id': self.edc_id.id,
        })
        return invoice_vals

    def _sync_get_order(self):
        self.ensure_one()
        if self.bypass_sync or not self.farmaku_order_id:
            return False
        parameter = "orders"
        auth = self._get_auth()
        url = self._get_url_with_id(parameter, self.farmaku_order_id)
        headers = {
            "Authorization": "Basic {auth}".format(auth=auth),
            "Content-Type": "application/json"
        }

        retries = 1
        success = False
        while not success and retries <= 3:
            try:
                r = requests.get(url=url, headers=headers, timeout=5)
                success = True
                if r.status_code == 200:
                    _logger.info('# Request Obtaining Get Order Info Success #')
                    _logger.info(r.text)
                    data = r.json()
                    self.sudo().write({
                        'order_status': data['orderStatus'],
                        'driver_name': data['delivery']['driverName'],
                        'driver_phone': data['delivery']['driverPhone'],
                        'driver_photo_url_path': data['delivery']['driverPhotoUrlPath'],
                        'driver_plate_number': data['delivery']['driverPlateNumber'],
                        'driver_vehicle_model': data['delivery']['driverVehicleModel'],
                        'tracking_url': data['delivery']['trackingUrl'],
                        'delivery_status': data['delivery']['deliveryStatus']
                    })
                    for line in self.order_line:
                        if line.product_id.purchase_method != 'purchase':
                            line.product_id.purchase_method = 'purchase'
            except Exception as e:
                _logger.error(str(e))

    def action_confirm(self):
        context = self.env.context.copy()
        context.update({
            'force_add': True
        })
        for rec in self:
            if rec._sync_confirm_order():
                super(SaleOrder, rec).action_confirm()
                rec.picking_ids.write({
                    'shipping_name': rec.shipping_name,
                    'shipping_service_name': rec.shipping_service_name,
                    'driver_plate_number': rec.driver_plate_number,
                })
                if rec.team_id.is_pos:
                    picking_ids = True
                    # coba assign ulang DO yang masih waiting
                    confirmed_picking_ids = rec.picking_ids.filtered(lambda pick: pick.state == 'confirmed')
                    if confirmed_picking_ids:
                        confirmed_picking_ids.action_assign()
                    while picking_ids:
                        picking_ids = rec.picking_ids.filtered(lambda pick: pick.state == 'assigned')
                        for picking_id in picking_ids:
                            for line in picking_id.move_line_ids:
                                line.write({'qty_done': line.product_uom_qty})
                            picking_id._action_done()
                rec._sync_get_order()
                self._auto_create_invoice(sale_id=rec)
        return True

    def action_cancel(self):
        context = self.env.context.copy()
        context.update({'disable_cancel_warning': True})
        self = self.with_context(context)
        for rec in self:
            if rec.cancel_reason_id and not self.env.context.get('skip_sync_to_fe'):
                if rec._sync_cancel_order():
                    super(SaleOrder, rec).action_cancel()
            else:
                super(SaleOrder, rec).action_cancel()
        return True

    def _prepare_confirmation_values(self):
        res = super(SaleOrder, self)._prepare_confirmation_values()
        if 'date_order' in res:
            res.pop('date_order')
        return res

    def sum_warehouse_product_quantity(self):
        warehouse_quantity = 0
        product_code = self._context.get('product_code', False)
        pharmacy_code = self._context.get('pharmacy_code', False)
        warehouse_id = self.env['stock.warehouse'].sudo().search([
            ('pharmacy_code', '=', pharmacy_code)
        ])
        quant_ids = self.env['stock.quant'].sudo().search([
            '|', ('product_id.default_code', '=', product_code),
            ('product_id.barcode', '=', product_code),
            ('location_id.usage', '=', 'internal'),
            ('location_id', '=', warehouse_id.lot_stock_id.id)])
        warehouses = {}
        for quant in quant_ids:
            if quant.location_id:
                if quant.location_id not in warehouses:
                    warehouses.update({quant.location_id: 0})
                warehouses[quant.location_id] += quant.available_quantity

        if warehouses:
            for location in warehouses:
                warehouse_quantity = warehouses[location]
        return warehouse_quantity

    def api_post_sale_order(self, vals):
        sale_order_id = self.env['sale.order']
        edc_id = self.env['electronic.data.capture']
        if vals:
            # proses ulang jika sudah pernah masuk sebelumnya dan gagal sync
            sale_order_id = self.sudo().search([
                '|',
                ('farmaku_order_id', '=', vals['OrderId']),
                ('invoice_number', '=', vals['InvoiceNumber']),
                ('state', 'not in', ['sale', 'done', 'cancel']),
            ], limit=1)
            if not sale_order_id:
                product_pricelist = self.env['product.pricelist'].sudo().search([])
                if product_pricelist:
                    product_pricelist_id = product_pricelist[0].id
                else:
                    raise ValidationError(_('No pricelist found.'))

                warehouse_id = self.env['stock.warehouse'].sudo().search([
                    ('pharmacy_code', '=', vals['PharmacyCode'])
                ], limit=1)
                if not warehouse_id:
                    raise ValidationError(_(f'Warehouse with pharmacy code {vals["PharmacyCode"]} not found.'))
                if not vals['Customer'].get('Phone') and not vals['Customer'].get('Name'):
                    if not warehouse_id.default_customer_id:
                        raise ValidationError(
                            _(f'Default customer for warehouse {warehouse_id.display_name} is not set.'))
                    customer_id = warehouse_id.default_customer_id
                else:
                    if vals['Customer']['Phone']:
                        if '*' in vals['Customer']['Phone']:
                            customer_id = self.env['res.partner'].sudo().search([
                                '|',
                                ('phone', '=', vals['Customer']['Phone']),
                                ('mobile', '=', vals['Customer']['Phone']),
                                ('name', '=', vals['Customer']['Name']),
                                ('street', '=', vals['Delivery']['Address']),
                            ], limit=1)
                        else:
                            customer_id = self.env['res.partner'].sudo().search([
                                '|',
                                ('phone', '=', vals['Customer']['Phone']),
                                ('mobile', '=', vals['Customer']['Phone']),
                            ], limit=1)
                    elif vals['Customer']['Name']:
                        customer_id = self.env['res.partner'].sudo().search([
                            ('name', '=', vals['Customer']['Name']),
                            ('street', '=', vals['Delivery']['Address']),
                        ], limit=1)
                    else:
                        customer_id = False
                    if customer_id:
                        customer_result = {
                            'type': 'contact',
                            'company_type': 'person',
                            'customer_rank': 1,
                            'name': vals['Customer']['Name'],
                            'display_name': vals['Customer']['Name'],
                            'phone': vals['Customer']['Phone'],
                            'mobile': vals['Customer']['Phone'],
                            'gender': vals['Customer']['Gender'],
                            'date_of_birth': dateutil.parser.isoparse(vals['Customer']['DateOfBirth']),
                            'street': vals['Delivery']['Address'],
                            'city': vals['Delivery']['City'],
                            'country_id': self.env['res.country'].sudo().search([
                                ('code', '=', 'ID')
                            ]).id,
                            'zip': vals['Delivery']['PostalCode'],
                            'partner_longitude': vals['Delivery']['Longitude'],
                            'partner_latitude': vals['Delivery']['Latitude'],
                            'property_product_pricelist': product_pricelist_id,
                            'company_id': False,
                        }
                        customer_id.sudo().write(customer_result)
                        customer_id._compute_display_name()
                    else:
                        customer_result = {
                            'type': 'contact',
                            'company_type': 'person',
                            'customer_rank': 1,
                            'name': vals['Customer']['Name'],
                            'display_name': vals['Customer']['Name'],
                            'phone': vals['Customer']['Phone'],
                            'mobile': vals['Customer']['Phone'],
                            'gender': vals['Customer']['Gender'],
                            'date_of_birth': dateutil.parser.isoparse(vals['Customer']['DateOfBirth'])
                            if vals['Customer']['DateOfBirth'] else False,
                            'street': vals['Delivery']['Address'],
                            'city': vals['Delivery']['City'],
                            'country_id': self.env['res.country'].sudo().search([
                                ('code', '=', 'ID')
                            ]).id,
                            'zip': vals['Delivery']['PostalCode'],
                            'partner_longitude': vals['Delivery']['Longitude'],
                            'partner_latitude': vals['Delivery']['Latitude'],
                            'property_product_pricelist': product_pricelist_id,
                            'company_id': False,
                        }
                        customer_id = self.env['res.partner'].sudo().create(customer_result)
                        customer_id._compute_display_name()
                if vals.get('SourceOrder'):
                    team_id = self.env['crm.team'].search([
                        ('code', '=', vals['SourceOrder']),
                        '|',
                        ('company_id', '=', warehouse_id.company_id.id),
                        ('company_id', '=', False),
                    ], limit=1)
                    if not team_id:
                        team_id = self.env['crm.team'].search([
                            '|',
                            ('company_id', '=', warehouse_id.company_id.id),
                            ('company_id', '=', False),
                        ], limit=1)
                else:
                    team_id = self.env['crm.team'].search([
                        '|',
                        ('company_id', '=', warehouse_id.company_id.id),
                        ('company_id', '=', False),
                    ], limit=1)
                if vals.get('EDC'):
                    edc_id = self.env['electronic.data.capture'].search([
                        ('name', '=', vals['EDC']),
                    ], limit=1)
                date_order = dateutil.parser.isoparse(vals['OrderDate'])
                user_tz = self.env.user.tz or 'Asia/Jakarta'
                date_order = pytz.timezone(user_tz).localize(date_order).astimezone(pytz.UTC)
                order_line = []
                for product in vals.get('Products', []):
                    rules_line = []
                    for rule in product.get('Rules', []):
                        rules_line.append((0, 0, {
                            'rule_type': rule['RuleType'],
                            'code': rule['Code'],
                            'latin_description': rule['Latin'],
                            'description': rule['Description'],
                        }))
                    if not product['IsConcoction']:
                        product_id = self.env['product.product'].sudo().search([
                            '|',
                            ('default_code', '=', product['ProductCode']),
                            ('barcode', '=', product['ProductCode'])
                        ])
                        if not product_id:
                            raise ValidationError(_(f'Product code {product["ProductCode"]} not found.'))
                        order_line.append((0, 0, {
                            'product_id': product_id.id,
                            'name': product_id.display_name,
                            'product_uom_qty': product['Quantity'],
                            'price_unit': product['UnitPrice'],
                            'normal_price': product.get('NormalPrice'),
                            'is_concoction': product['IsConcoction'],
                            'product_uom': product_id.uom_id.id,
                            'note': product['Note'],
                            'rules_line': rules_line,
                        }))
                    else:
                        for composition in product.get('Compositions', []):
                            product_id = self.env['product.product'].sudo().search([
                                '|',
                                ('default_code', '=', composition['ProductCode']),
                                ('barcode', '=', composition['ProductCode'])
                            ])
                            if not product_id:
                                raise ValidationError(_(f'Product code {composition["ProductCode"]} not found.'))
                            order_line.append((0, 0, {
                                'product_id': product_id.id,
                                'name': product_id.display_name,
                                'product_uom_qty': product['Quantity'] * composition['Quantity'],
                                'price_unit': composition.get('UnitPrice', product_id.list_price),
                                'normal_price': composition.get('NormalPrice'),
                                'is_concoction': False,
                                'product_uom': product_id.uom_id.id,
                                'note': composition['Note'],
                                'rules_line': rules_line,
                            }))
                order_result = {
                    'bypass_sync': vals.get('bypass_sync', False),
                    'team_id': team_id.id,
                    'is_from_api': True,
                    'is_need_to_enter_airway_bill': vals['IsNeedToEnterAirwayBill'],
                    'partner_id': customer_id.id,
                    'farmaku_order_id': vals['OrderId'],
                    'origin': vals['OrderNumber'],
                    'order_number': vals['OrderNumber'],
                    'invoice_number': vals['InvoiceNumber'],
                    'grand_total_price': vals['GrandTotalPrice'],
                    'date_order': date_order.strftime('%Y-%m-%d %H:%M:%S'),
                    'has_concoction': vals['HasConcoction'],
                    'pharmacy_code': vals['PharmacyCode'],
                    'pharmacy_name': vals['PharmacyName'],
                    'shipping_price': vals['Delivery']['ShippingPrice'],
                    'shipping_discount': vals['Delivery']['ShippingDiscount'],
                    'shipping_distance': vals['Delivery']['ShippingDistance'],
                    'shipping_note': vals['Delivery'].get('ShippingNote'),
                    'shipping_name': vals['Delivery']['ShippingName'],
                    'shipping_service_name': vals['Delivery']['ShippingServiceName'],
                    'recipient_name_web': vals['Delivery'].get('RecipientName'),
                    'recipient_phone_web': vals['Delivery'].get('RecipientPhone'),
                    'recipient_address_web': vals['Delivery'].get('Address'),
                    'warehouse_id': warehouse_id.id,
                    'is_backorder': vals.get('IsBackOrder'),
                    'payment_method': vals.get('PaymentMethod'),
                    'order_line': order_line,
                    'company_id': warehouse_id.company_id.id,
                    'edc_id': edc_id.id,
                }
                sale_order_id = self.sudo().create(order_result)
        return sale_order_id

    def api_cancel_sale_order(self, vals):
        order_id = self.env['sale.order'].search([
            ('order_number', '=', vals['OrderNumber']),
            ('invoice_number', '=', vals['InvoiceNumber']),
            ('state', '!=', 'cancel'),
        ], limit=1)
        farmaku_cancel_reason_id = vals.get('cancelReasonId')
        cancel_note = vals.get('cancelNote')
        if farmaku_cancel_reason_id:
            cancel_reason_id = self.env['cancel.reason'].search([
                ('farmaku_cancel_reason_id', '=', farmaku_cancel_reason_id)
            ], limit=1)
            if cancel_reason_id:
                order_id.write({
                    'cancel_reason_id': cancel_reason_id.id,
                    'cancel_note': cancel_note,
                })
        if not order_id:
            raise ValidationError(_(f'Order with order number {vals["OrderNumber"]} '
                                    f'and invoice number {vals["InvoiceNumber"]} not found.'))
        order_id.with_context(skip_sync_to_fe=True).action_cancel()
        return order_id

    def _get_auth(self):
        server_key = self.env['ir.config_parameter'].sudo().get_param('farmaku_server_key')
        auth = base64.b64encode(bytes("{auth}{colon}".format(auth=server_key, colon=":"), 'utf-8')).decode('UTF-8')
        return auth

    def _get_url(self, parameter):
        url = self.env['ir.config_parameter'].sudo().get_param('farmaku_url')
        url_odoo = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if url == 'https://pharmacy-api.securerx.id' and url_odoo != 'https://farmaku.odoo.com':
            raise ValidationError(_('Url API Production Farmaku can use in Url Production Odoo'))
        endpoint = '/'.join(
            [url, self.env['ir.config_parameter'].sudo().get_param('farmaku_{param}_endpoint'.format(param=parameter))])
        return endpoint

    def _get_url_with_id(self, parameter, id):
        url = self.env['ir.config_parameter'].sudo().get_param('farmaku_url')
        url_odoo = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if url == 'https://pharmacy-api.securerx.id' and url_odoo != 'https://farmaku.odoo.com':
            raise ValidationError(_('Url API Production Farmaku can use in Url Production Odoo'))
        endpoint = '/'.join(
            [url, self.env['ir.config_parameter'].sudo().get_param('farmaku_{param}_endpoint'.format(param=parameter))])
        endpoint_with_id = endpoint.replace("{id}", str(id))
        return endpoint_with_id

    def _sync_confirm_order(self):
        self.ensure_one()
        if self.bypass_sync or not self.farmaku_order_id:
            return True
        parameter = "orders_proses"
        auth = self._get_auth()
        url = self._get_url_with_id(parameter, self.farmaku_order_id)
        headers = {
            "Authorization": "Basic {auth}".format(auth=auth),
            "Content-Type": "application/json"
        }
        body = {}
        retries = 1
        success = False
        error_message = ''
        while not success and retries <= 3:
            try:
                r = requests.put(url=url, headers=headers, timeout=5)
                success = True
                _logger.info('# Request Obtaining Proses Order #')
                self.env.user.create_connector_log(
                    url=url,
                    method='PUT',
                    headers=headers,
                    body=body,
                    response=r,
                    response_body=False,
                )
                if r.status_code == 200:
                    _logger.info('# Request Obtaining Proses Order Success #')
                    _logger.info(r.text)
                elif r.status_code == 404:
                    error_message = '404 not found.'
                else:
                    _logger.warning('# Request Obtaining Proses Order Failed, code {code} #'.format(code=r.status_code))
                    _logger.warning(r.text)
                    result = r.json()
                    detail = result.get('detail')
                    if isinstance(detail, str):
                        error_message = detail
                        if 'ErrorMessage' in detail:
                            error_message = ast.literal_eval(detail.replace('null', '""'))[0]['ErrorMessage']
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
        if error_message:
            self.message_post(body=_(f'Error: {error_message}'))
        #     raise ValidationError(_(error_message))
        return not bool(error_message)

    def _sync_cancel_order(self):
        self.ensure_one()
        if self.bypass_sync or not self.farmaku_order_id:
            return True
        parameter = "orders_cancel"
        auth = self._get_auth()
        url = self._get_url_with_id(parameter, self.farmaku_order_id)
        headers = {
            "Authorization": "Basic {auth}".format(auth=auth),
            "Content-Type": "application/json"
        }
        body = {
            'cancelReasonId': self.cancel_reason_id.farmaku_cancel_reason_id or '',
            'cancelNote': self.cancel_note or '',
        }
        retries = 1
        success = False
        error_message = ''
        while not success and retries <= 3:
            try:
                r = requests.put(url=url, headers=headers, json=body, timeout=5)
                success = True
                _logger.info('# Request Obtaining Get Pharmacies Product #')
                self.env.user.create_connector_log(
                    url=url,
                    method='PUT',
                    headers=headers,
                    body=body,
                    response=r,
                    response_body=False,
                )
                if r.status_code == 200:
                    _logger.info('# Request Obtaining Get Pharmacies Product Success #')
                    _logger.info(r.text)
                elif r.status_code == 404:
                    error_message = '404 not found.'
                else:
                    _logger.warning('# Request Obtaining Cancel Order Failed, code {code} #'.format(code=r.status_code))
                    _logger.warning(r.text)
                    result = r.json()
                    detail = result.get('detail')
                    if isinstance(detail, str):
                        error_message = detail
                        if 'ErrorMessage' in detail:
                            error_message = ast.literal_eval(detail.replace('null', '""'))[0]['ErrorMessage']
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
        if error_message:
            self.message_post(body=_(f'Error: {error_message}'))
        return not bool(error_message)

    def _sync_change_warehouse(self, order_id):
        sale_order_id = self.sudo().search([
            ('farmaku_order_id', '=', order_id),
            ('state', 'not in', ['done', 'cancel'])
        ], limit=1)
        parameter = "change_warehouse"
        auth = self._get_auth()
        url = self._get_url_with_id(parameter, order_id)
        headers = {
            "Authorization": "Basic {auth}".format(auth=auth),
            "Content-Type": "application/json"
        }
        body = {
            'pharmacyCode': sale_order_id.warehouse_id.pharmacy_code,
        }
        retries = 1
        success = False
        while not success and retries <= 3:
            try:
                r = requests.put(url=url, headers=headers, json=body, timeout=5)
                success = True
                _logger.info('# Request Obtaining Change Order Warehouse #')
                self.env.user.create_connector_log(
                    url=url,
                    method='PUT',
                    headers=headers,
                    body=body,
                    response=r,
                    response_body=False,
                )
                if r.status_code == 200:
                    _logger.info('# Request Obtaining Change Order Warehouse Success #')
                    _logger.info(r.text)
                elif r.status_code == 404:
                    error_message = '404 not found.'
                else:
                    _logger.warning(
                        '# Request Obtaining Change Order Warehouse Failed, code {code} #'.format(code=r.status_code))
                    _logger.warning(r.text)
                    return {}
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

    def button_get_order(self):
        return self.env.ref('asb_rest_api.order').report_action(self.ids, config=False)

    def get_order_report(self):
        return []

    def action_refund(self):
        context = self.env.context.copy()
        context.update({'skip_refund': True})
        self = self.with_context(context)
        for rec in self.filtered(lambda s: s.state in ('sale', 'done')):
            rec.return_picking()
            for invoice_id in rec.invoice_ids:
                if invoice_id.state == 'posted':
                    payment_ids = self.env['account.payment']
                    for partial, amount, counterpart_line in invoice_id._get_reconciled_invoices_partials():
                        payment_ids |= counterpart_line.move_id.payment_id
                    for payment_id in payment_ids:
                        if payment_id.state == 'posted':
                            payment_id.action_draft()
                        if payment_id.state == 'draft':
                            payment_id.action_cancel()
                    reverse_id = self.env['account.move.reversal'].create({
                        'refund_method': 'refund',
                        'date_mode': 'custom',
                        'date': fields.Date.today(),
                        'move_ids': [(6, 0, invoice_id.ids)],
                    })
                    reverse_id.with_context(default_auto_post=True).reverse_moves()
                    rec.invoice_ids.filtered(
                        lambda i: i.move_type == 'out_refund'
                        and i.state == 'draft'
                    )._post()
                if invoice_id.state == 'draft':
                    invoice_id.button_cancel()

    def _auto_create_invoice(self, sale_id):
        exclude_sales_team_ids = []
        exclude_sales_team = self.env['ir.config_parameter'].sudo().get_param(
            'asb_rest_api.exclude_sales_team_auto_create_invoice')
        if exclude_sales_team:
            exclude_sales_team = exclude_sales_team.replace(' ', '').split(',')
            exclude_sales_team_ids = [int(team_id) for team_id in exclude_sales_team]
        if sale_id.team_id.id in exclude_sales_team_ids:
            sale_id.message_post(body=_(f'Does not automatically create invoices because it excludes the sales team'))
        if sale_id.invoice_status != 'to invoice':
            sale_id.message_post(body=_(f'Does not automatically create invoices because nothing to invoice'))
        if sale_id.team_id.id not in exclude_sales_team_ids and sale_id.invoice_status == 'to invoice':
            invoice = self.env["sale.advance.payment.inv"].create({})
            invoice.with_context(active_ids=sale_id.ids).create_invoices()
            if not sale_id.invoice_ids:
                sale_id.message_post(body=_(f'Does not automatically create invoices because access error'))
            for invoice in sale_id.invoice_ids.filtered(lambda i: i.state == 'draft'):
                invoice.with_company(invoice.company_id).sudo().action_post()
