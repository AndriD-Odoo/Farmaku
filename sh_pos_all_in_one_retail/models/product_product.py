from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.depends('stock_quant_ids.quantity', 'stock_quant_ids.reserved_quantity')
    def _get_qty_available_real(self):
        for rec in self:
            qty_available_real = 0
            warehouse_ids = self.env['stock.warehouse'].search([])
            lot_stock_ids = warehouse_ids.lot_stock_id
            location_ids = self.env['stock.location'].search([('id', 'child_of', lot_stock_ids.ids)])
            if location_ids:
                query = f"""
                    SELECT
                        SUM(quantity-reserved_quantity) as available_qty,
                        SUM(quantity) as quantity
                    FROM
                        stock_quant
                    WHERE
                        product_id = {rec.id}
                        AND location_id in ({','.join(str(loc_id) for loc_id in location_ids.ids)})
                """
                self.env.cr.execute(query)
                result = self.env.cr.dictfetchone()
                if result:
                    qty_available_real = result['available_qty']
            rec.qty_available_real = qty_available_real

    qty_available_real = fields.Float(
        string='Qty Available',
        store=True,
        compute='_get_qty_available_real')

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if args:
            if ['available_in_pos', '=', True] in args and order == 'sequence ASC, default_code ASC, name ASC':
                order = 'qty_available_real DESC, sequence ASC, default_code ASC, name ASC'
        res = super(ProductProduct, self).search(args=args, offset=offset, limit=limit, order=order, count=count)
        return res
