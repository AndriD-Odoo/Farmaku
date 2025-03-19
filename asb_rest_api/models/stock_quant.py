from odoo import models, fields, api, _


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    product_code = fields.Char(string='Product Code', related='product_id.default_code', store=True)

    @api.model
    def create(self, vals):
        res = super(StockQuant, self).create(vals)
        return res

    def write(self, vals):
        res = super(StockQuant, self).write(vals)
        return res
