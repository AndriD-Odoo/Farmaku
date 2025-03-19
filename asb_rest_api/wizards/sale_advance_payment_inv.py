from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import pytz


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def _prepare_invoice_values(self, order, name, amount, so_line):
        invoice_vals = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(
            order=order, name=name, amount=amount, so_line=so_line)
        if order.invoice_number:
            invoice_vals['ref'] = order.invoice_number
        user_tz = self.env.user.tz or 'Asia/Jakarta'
        if order.date_order:
            invoice_vals['invoice_date'] = pytz.UTC.localize(order.date_order).astimezone(pytz.timezone(user_tz))
        if order.team_id:
            partner_bank_id = order.get_partner_bank_id()
            invoice_vals['partner_bank_id'] = partner_bank_id
        invoice_vals.update({
            'order_number': order.order_number,
            'payment_method': order.payment_method,
            'edc_id': order.edc_id.id,
        })
        return invoice_vals
