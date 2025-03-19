from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sales_conversion_qty = fields.Float(
        string='Konversi Jual',
        required=False)
