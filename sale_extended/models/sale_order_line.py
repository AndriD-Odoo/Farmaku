from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_uom_qty = fields.Float(digits='Product Unit of Measure Integer')
    qty_delivered = fields.Float(digits='Product Unit of Measure Integer')
    qty_invoiced = fields.Float(digits='Product Unit of Measure Integer')
    normal_price = fields.Float(
        string='Normal Price',
        digits='Product Price',
        required=False)

    def product_uom_change(self):
        # tidak perlu ubah harga ketika edit qty
        current_price_unit = self.price_unit
        super().product_uom_change()
        if current_price_unit:
            self.price_unit = current_price_unit
