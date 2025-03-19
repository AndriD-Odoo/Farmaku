from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    pharmacy_code = fields.Char(string='Pharmacy Code')
