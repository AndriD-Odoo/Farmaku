from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends(
        'invoice_line_ids.dpp_price',
        'invoice_line_ids.quantity',
    )
    def _get_dpp_total(self):
        for rec in self:
            dpp_total = 0
            for line in rec.invoice_line_ids:
                sale_line_ids = line.sale_line_ids.filtered(lambda l: l.order_id.state != 'cancel')
                if sale_line_ids:
                    sale_line_id = sale_line_ids[0]
                    if sale_line_id.product_uom_qty:
                        dpp_price = sale_line_id.price_subtotal / sale_line_id.product_uom_qty
                        dpp_price = dpp_price * 11 / 12
                        dpp_total += (dpp_price * line.quantity)
            rec.dpp_total = dpp_total

    dpp_total = fields.Monetary(
        string='DPP Total',
        compute_sudo=True,
        compute='_get_dpp_total')

    def write(self, values):
        res = super(AccountMove, self).write(values)
        for rec in self:
            if 'state' in values and rec.move_type == 'out_refund':
                sale_ids = rec.invoice_line_ids.mapped('sale_line_ids.order_id')
                if sale_ids:
                    sale_ids.compute_refund_status()
        return res
