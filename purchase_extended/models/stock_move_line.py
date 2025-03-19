from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    uom_po_id = fields.Many2one(related='product_id.uom_po_id', string='UoM PO')
