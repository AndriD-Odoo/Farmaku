from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    rules_line = fields.One2many('product.rule.sale', 'so_line_id', string='Rules')
    compositions_line = fields.One2many('product.composition.line', 'so_line_id', string='Compositions')
    note = fields.Char(string='note')
    is_concoction = fields.Boolean(string='Concoction ?')
