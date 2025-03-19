from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    @api.depends(
        'sale_line_ids.order_id.state',
        'sale_line_ids.dpp_price',
        'quantity',
    )
    def _compute_dpp_amount(self):
        for rec in self:
            dpp_price = 0
            sale_line_ids = rec.sale_line_ids.filtered(lambda l: l.order_id.state != 'cancel')
            if sale_line_ids:
                sale_line_id = sale_line_ids[0]
                if sale_line_id.product_uom_qty:
                    dpp_price = sale_line_id.price_subtotal / sale_line_id.product_uom_qty
                    dpp_price = dpp_price * 11 / 12
            rec.dpp_price = dpp_price
            rec.dpp_subtotal = dpp_price * rec.quantity

    dpp_price = fields.Float(
        string='DPP', 
        digits='Product Price',
        compute='_compute_dpp_amount',
        compute_sudo=True,
        store=False)
    dpp_subtotal = fields.Float(
        string='Subtotal DPP',
        digits='Product Price',
        compute='_compute_dpp_amount',
        compute_sudo=True,
        store=False)
