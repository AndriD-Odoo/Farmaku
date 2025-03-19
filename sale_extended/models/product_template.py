from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, values):
        res = super(ProductTemplate, self).write(values)
        for rec in self:
            if 'invoice_policy' in values:
                sale_line_ids = self.env['sale.order.line'].sudo().search([
                    ('product_id', 'in', rec.product_variant_ids.ids),
                    ('invoice_status', 'in', ['no', 'to invoice']),
                ])
                sale_line_ids._get_to_invoice_qty()
        return res
