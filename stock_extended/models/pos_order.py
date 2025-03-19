from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def write(self, values):
        res = super(PosOrder, self).write(values)
        for rec in self:
            if 'state' in values:
                product_ids = rec.mapped('order_line.product_id')
                self.env['stock.warehouse.orderpoint'].sudo().update_last_sale_date_by_product_warehouse(
                    product_ids, rec.session_id.config_id.picking_type_id.warehouse_id
                )
        return res
