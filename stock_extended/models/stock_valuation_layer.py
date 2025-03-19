from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    unit_cost = fields.Monetary(group_operator=False)
