from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def write(self, values):
        res = super(SaleOrder, self).write(values)
        for rec in self:
            if 'state' in values:
                product_ids = rec.mapped('order_line.product_id')
                self.env['stock.warehouse.orderpoint'].sudo().update_last_sale_date_by_product_warehouse(
                    product_ids, rec.warehouse_id
                )
        return res
