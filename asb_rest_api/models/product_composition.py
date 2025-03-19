from odoo import models, fields, api


class ProductCompositionLine(models.Model):
    _name = 'product.composition.line'
    _description = 'Product Composition Line'

    product_name = fields.Char(string='Rule type')
    product_code = fields.Char(string='code')
    uom = fields.Char(string='Latin Description')
    quantity = fields.Integer(string='Quantity')
    note = fields.Text(string='Note')
    so_line_id = fields.Many2one('sale.order.line', string='SO Line', ondelete='cascade')
