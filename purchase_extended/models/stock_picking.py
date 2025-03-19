from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    created_purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        related='move_lines.created_purchase_id')
