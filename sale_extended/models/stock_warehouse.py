from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    default_customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Default Customer',
        domain=[('customer_rank', '>', 0)])
