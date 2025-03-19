from odoo import http, modules
from odoo.http import request, route
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil import tz

from odoo.addons.ms_rest_api.models.common import (
    _logger,
    success_response,
    error_response,
    authentication,
    check_mandatory_fields
)


def set_tz(date_convert, tz_from, tz_to):
    res = date_convert
    if date_convert:
        res = date_convert.replace(tzinfo=tz.gettz(tz_from))
        res = res.astimezone(tz.gettz(tz_to))
    return res


class ApiSaleOrder(http.Controller):
    
    @route('/api/v1/order', methods=['POST'], type='json', auth='public', csrf=False)
    @authentication
    def post_sale_order(self):
        vals = http.request.jsonrequest
        _logger.info(f'\n{vals}')
        error_detail = {}
        data = {}
        try:
            exist_order_id = request.env['sale.order'].sudo().search([
                '|',
                ('farmaku_order_id', '=', vals['OrderId']),
                ('invoice_number', '=', vals['InvoiceNumber']),
                ('state', 'in', ['sale', 'done']),
                ('refund_status', '!=', 'full'),
            ], limit=1)
            if exist_order_id:
                data.update({
                    'order_id': exist_order_id.farmaku_order_id or '',
                    'sale_number': exist_order_id.name or '',
                })
            else:
                order_id = request.env['sale.order'].sudo().api_post_sale_order(vals=vals)
                time_now = set_tz(fields.Datetime.now(), 'UTC', http.request.env.user.tz or 'Asia/Jakarta').replace(
                    tzinfo=None)
                list_under_qty = []
                if not vals.get('IsBackOrder'):
                    for line in order_id.order_line:
                        if line.product_id.type != 'product':
                            continue
                        inventory_context = {
                            'product_code': line.product_id.default_code,
                            'pharmacy_code': vals['PharmacyCode']
                        }
                        quantity_product_warehouse = http.request.env['sale.order'].sudo().with_context(
                            inventory_context).sum_warehouse_product_quantity()

                        if line.product_uom_qty > quantity_product_warehouse:
                            list_under_qty.append(line.product_id.display_name)
                if (time_now.hour + (time_now.minute / 60) <= http.request.env.company.opening_hours) or \
                        (time_now.hour + (time_now.minute / 60) > http.request.env.company.closing_hours):
                    cancel_reason_id = http.request.env['cancel.reason'].sudo().get_cancel_reason_by_id(
                        farmaku_cancel_reason_id=3)
                    order_id.write({
                        'cancel_reason_id': cancel_reason_id.id
                    })
                    order_id.action_cancel()
                    data.update({
                        'order_id': order_id.farmaku_order_id or '',
                        'sale_number': order_id.name or '',
                    })
                elif list_under_qty:
                    order_id.message_post(body=_(f'Out of stock {", ".join(list_under_qty)}.'))
                    cancel_reason_id = http.request.env['cancel.reason'].sudo().get_cancel_reason_by_id(
                        farmaku_cancel_reason_id=2)
                    order_id.write({
                        'cancel_reason_id': cancel_reason_id.id
                    })
                    order_id.action_cancel()
                    for line in order_id.order_line:
                        if line.product_id.type != 'product':
                            continue
                        line.product_id._sync_update_stock(pharmacy_code=order_id.warehouse_id.pharmacy_code)
                    data.update({
                        'order_id': order_id.farmaku_order_id or '',
                        'sale_number': order_id.name or '',
                    })
                else:
                    order_id.action_confirm()
                    data.update({
                        'order_id': order_id.farmaku_order_id or '',
                        'sale_number': order_id.name or '',
                    })
        except Exception as e:
            error_detail.update({
                'status_code': 500,
                'error_type': 'general',
                'error_message': str(e),
            })
        if error_detail:
            return error_response(
                status_code=error_detail['status_code'],
                error_message=error_detail['error_message'],
                error_type=error_detail.get('error_type')
            )
        else:
            return success_response(
                status_code=201,
                result=data
            )

    @route('/api/v1/order/cancel', methods=['POST'], type='json', auth='public', csrf=False)
    @authentication
    def cancel_sale_order(self):
        vals = http.request.jsonrequest
        _logger.info(f'\n{vals}')
        error_detail = {}
        data = {}
        try:
            mandatory_fields = [
                'OrderNumber',
                'InvoiceNumber',
            ]
            need_fields = check_mandatory_fields(
                mandatory_fields=mandatory_fields,
                val=vals
            )
            if need_fields:
                error_detail.update({
                    'status_code': 400,
                    'error_type': 'mandatory_fields',
                    'error_message': ', '.join(need_fields),
                })
            else:
                order_id = request.env['sale.order'].sudo().api_cancel_sale_order(vals=vals)
                data.update({
                    'order_id': order_id.farmaku_order_id or '',
                })
        except Exception as e:
            error_detail.update({
                'status_code': 500,
                'error_type': 'general',
                'error_message': str(e),
            })
        if error_detail:
            return error_response(
                status_code=error_detail['status_code'],
                error_message=error_detail['error_message'],
                error_type=error_detail.get('error_type')
            )
        else:
            return success_response(
                status_code=200,
                result=data
            )

    @route('/api/v1/order/<int:farmaku_order_id>', methods=['GET'], type='http', auth='public', csrf=False)
    @authentication
    def get_so_numbers(self, farmaku_order_id):
        _logger.info(f'\n{farmaku_order_id}')
        error_detail = {}
        data = {}
        try:
            order_id = request.env['sale.order'].sudo().search([
                ('farmaku_order_id', '=', farmaku_order_id),
                ('state', '!=', 'cancel'),
            ], limit=1)
            if not order_id:
                order_id = request.env['sale.order'].sudo().search([
                    ('farmaku_order_id', '=', farmaku_order_id),
                ], limit=1)
            if not order_id:
                error_detail.update({
                    'status_code': 404,
                    'error_type': 'not_found',
                    'error_message': f'Order with order ID {farmaku_order_id} not found.',
                })
            data.update({
                'sale_number': order_id.name or '',
            })
        except Exception as e:
            error_detail.update({
                'status_code': 500,
                'error_type': 'general',
                'error_message': str(e),
            })
        if error_detail:
            return error_response(
                status_code=error_detail['status_code'],
                error_message=error_detail['error_message'],
                error_type=error_detail.get('error_type')
            )
        else:
            return success_response(
                status_code=200,
                result=data
            )

    @route('/api/v1/order', methods=['PUT'], type='json', auth='public', csrf=False)
    @authentication
    def change_sale_order(self):
        vals = http.request.jsonrequest
        _logger.info(f'\n{vals}')
        error_detail = {}
        data = {}
        farmaku_order_id = vals.get('OrderId')
        pharmacy_code = vals.get('PharmacyCode')
        warehouse_id = request.env['stock.warehouse'].sudo().search([
            ('pharmacy_code', '=', pharmacy_code)
        ])
        product_detail = vals.get('Products')
        try:
            order_id = request.env['sale.order'].sudo().search([
                ('farmaku_order_id', '=', farmaku_order_id),
                ('state', '!=', 'cancel'),
            ], limit=1)
            if not order_id:
                error_detail.update({
                    'status_code': 404,
                    'error_type': 'not_found',
                    'error_message': f'Order with order ID {farmaku_order_id} not found.',
                })
            elif not warehouse_id:
                error_detail.update({
                    'status_code': 404,
                    'error_type': 'not_found',
                    'error_message': f'Pharmacy code {pharmacy_code} not found.',
                })
            else:
                current_stock = {}
                if warehouse_id.id == order_id.warehouse_id.id:
                    for line_id in order_id.order_line:
                        product_code = line_id.product_id.default_code or line_id.product_id.barcode
                        current_stock[product_code] = current_stock.get(
                            product_code, 0) + line_id.product_uom._compute_quantity(
                            line_id.product_uom_qty, line_id.product_id.uom_id)
                list_under_qty = []
                if product_detail:
                    for product in product_detail:
                        if not product['IsConcoction']:
                            product_id = request.env['product.product'].sudo().search([
                                '|',
                                ('default_code', '=', product['ProductCode']),
                                ('barcode', '=', product['ProductCode'])
                            ])
                            if not product_id:
                                error_detail.update({
                                    'status_code': 404,
                                    'error_type': 'not_found',
                                    'error_message': f'Product code {product["ProductCode"]} not found.',
                                })
                                break
                            if product_id.type != 'product':
                                continue
                            inventory_context = {
                                'product_code': product_id.default_code or product_id.barcode,
                                'pharmacy_code': warehouse_id.pharmacy_code
                            }
                            quantity_product_warehouse = http.request.env['sale.order'].sudo().with_context(
                                inventory_context).sum_warehouse_product_quantity()
                            quantity_product_warehouse = quantity_product_warehouse + current_stock.get(
                                product['ProductCode'], 0)
                            # FIXME: tidak memperhitungkan UoM
                            if quantity_product_warehouse < product['Quantity']:
                                list_under_qty.append(product_id.display_name)
                if list_under_qty:
                    error_detail.update({
                        'status_code': 400,
                        'error_type': 'out_of_stock',
                        'error_message': ', '.join(list_under_qty),
                    })
                if not error_detail:
                    order_id.with_context(skip_sync_to_fe=True).action_cancel()
                    order_id.action_draft()
                    if order_id.warehouse_id.id != warehouse_id.id:
                        if order_id.warehouse_id.default_customer_id.id == order_id.partner_id.id:
                            order_id.write({'partner_id': warehouse_id.default_customer_id.id})
                        order_id.with_context(skip_sync_to_fe=True).write({'warehouse_id': warehouse_id.id})
                    order_line = []
                    for product in product_detail:
                        rules_line = []
                        for rule in product.get('Rules', []):
                            rules_line.append((0, 0, {
                                'rule_type': rule['RuleType'],
                                'code': rule['Code'],
                                'latin_description': rule['Latin'],
                                'description': rule['Description'],
                            }))
                        if not product['IsConcoction']:
                            product_id = request.env['product.product'].sudo().search([
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
                                product_id = request.env['product.product'].sudo().search([
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
                    order_id.order_line = False
                    order_id.write({
                        'order_line': order_line
                    })
                    order_id.action_confirm()
                    data.update({
                        'order_id': order_id.farmaku_order_id or '',
                        'sale_number': order_id.name or '',
                    })
        except Exception as e:
            error_detail.update({
                'status_code': 500,
                'error_type': 'general',
                'error_message': str(e),
            })
        if error_detail:
            return error_response(
                status_code=error_detail['status_code'],
                error_message=error_detail['error_message'],
                error_type=error_detail.get('error_type')
            )
        else:
            return success_response(
                status_code=200,
                result=data
            )
