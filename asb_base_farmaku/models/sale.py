from odoo import models, fields, api, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('price_unit', 'tax_id', 'product_uom_qty')
    def _compute_dpp_amount(self):
        for rec in self:
            dpp_price = 0
            if rec.product_uom_qty:
                dpp_price = rec.price_subtotal / rec.product_uom_qty
                dpp_price = dpp_price * 11 / 12
            rec.dpp_price = dpp_price
            rec.dpp_subtotal = dpp_price * rec.product_uom_qty

    dpp_price = fields.Float(
        string='DPP',
        digits='Product Price',
        compute='_compute_dpp_amount',
        compute_sudo=True,
        store=False
    )
    dpp_subtotal = fields.Float(
        string='Subtotal DPP',
        digits='Product Price',
        compute='_compute_dpp_amount',
        compute_sudo=True,
        store=False)
