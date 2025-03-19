from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    allow_less_than_expiration_time = fields.Boolean(
        string='Allow Less Than Expiration Time',
        copy=False)

    def write(self, values):
        res = super(StockMove, self).write(values)
        return res
