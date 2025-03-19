from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import pytz
import requests


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def get_yesterday(self):
        return pytz.UTC.localize(fields.Datetime.now()).astimezone(pytz.timezone(self.env.user.tz or 'Asia/Jakarta')) \
            - timedelta(days=1)

    def _send_pos_order_data(self, trx_date=''):
        if not trx_date:
            trx_date = self.get_yesterday().strftime("%Y-%m-%d")
            # trx_date = '2022-02-09'
        start_date = datetime.strptime(trx_date, "%Y-%m-%d") - timedelta(days=1)
        start_date = start_date.strftime("%Y-%m-%d 17:00:00")
        end_date = trx_date + " 17:00:00"
        order_ids = self.env['pos.order'].search([
            ('state', 'in', ['paid', 'done', 'invoiced']),
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date),
        ])
        if not order_ids:
            raise ValidationError(_(f'No POS data found at {trx_date}.'))
        parameter = "send_pos_data"
        auth = self.env['sale.order']._get_auth()
        url = self.env['sale.order']._get_url(parameter)
        headers = {
            "Authorization": "Basic {auth}".format(auth=auth),
            "Content-Type": "application/json"
        }
        orders = []
        for order_id in order_ids:
            products = []
            payments = []
            tot_discount = 0.00
            tot_price = 0.00
            for line_id in order_id.lines:
                products.append({
                    'productCode': line_id.product_id.default_code or '',
                    'productName': line_id.product_id.name,
                    'qty': int(line_id.qty),
                    'unitPrice': line_id.price_unit,
                    'uom': line_id.product_uom_id.name,
                    'subTotal': line_id.price_subtotal_incl,
                })
                if line_id.discount:
                    tot_discount += line_id.price_unit * line_id.discount / 100 * line_id.qty
                tot_price += line_id.price_unit * line_id.qty
            order_date = ''
            birth_date = ''
            if order_id.date_order:
                order_date = pytz.UTC.localize(order_id.date_order).astimezone(pytz.timezone(self.env.user.tz or 'Asia/Jakarta'))
                order_date = order_date.isoformat()
            if order_id.partner_id.date_of_birth:
                birth_date = pytz.UTC.localize(order_id.partner_id.date_of_birth).astimezone(pytz.timezone(self.env.user.tz or 'Asia/Jakarta'))
                birth_date = birth_date.isoformat()
            for payment_id in order_id.payment_ids:
                payments.append({
                    'paymentMethod': payment_id.payment_method_id.display_name,
                    'paymentAmount': payment_id.amount,
                })
            orders.append({
                'requestId': str(order_id.id),
                'receiptNumber': order_id.pos_reference or '',
                'orderDate': order_date,
                'orderStatus': order_id.state,
                'pharmacyCode': order_id.session_id.config_id.picking_type_id.warehouse_id.pharmacy_code or '',
                'paymentMethod': ', '.join(order_id.payment_ids.mapped('payment_method_id.name')) if order_id.payment_ids else '',
                'isReturnOrder': order_id.is_return_order,
                'isExchangeOrder': order_id.is_exchange_order,
                'returnReferenceNumber': order_id.old_pos_reference or '',
                'totalPrice': tot_price,
                'totalDiscount': tot_discount,
                'grandTotal': order_id.amount_total,
                'customer': {
                    'uniqueId': str(order_id.partner_id.id or ''),
                    'name': order_id.partner_id.name or '',
                    'gender': order_id.partner_id.gender or '',
                    'dateOfBirth': birth_date,
                    'email': order_id.partner_id.email or '',
                    'phone': order_id.partner_id.phone or '',
                },
                'products': products,
                'payments': payments,
            })
        body = {'orders': orders}
        response = requests.post(url=url, headers=headers, json=body)
        if response.status_code != 200:
            raise ValidationError(_(f'Data: {str(body)}\n\nStatus: {response.status_code}, Detail: {response.text}'))
