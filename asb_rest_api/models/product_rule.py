from odoo import models, fields, api


class ProductRuleSale(models.Model):
    _name = 'product.rule.sale'
    _description = 'Product Rules'

    rule_type = fields.Char(string='Rule type')
    code = fields.Char(string='code')
    latin_description = fields.Char(string='Latin Description')
    description = fields.Char(string='description')
    so_line_id = fields.Many2one('sale.order.line', string='SO Line', ondelete='cascade')