from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'
    _description = 'Stock Move'

    purchase_qty = fields.Float(string='Quantity', compute='_compute_purchase_qty', store=True,)
    purchase_uom_id = fields.Many2one(related='purchase_line_id.product_uom', store=True, string='Purchase UoM')


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', required=True, domain="[]")
    uom_id = fields.Many2one(related="product_id.uom_id", string='Default Product UoM')
