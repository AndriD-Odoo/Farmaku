# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    normal_price = fields.Float(string='Normal Price', digits='Product Price')
    discount_price = fields.Float(string='Discount Price', digits='Product Price')
    product_uom_line_ids = fields.One2many('product.uom.line', 'product_tmpl_id', string='Product Uom')
    uom_exist_ids = fields.Many2many('uom.uom', string='Uom Exist', compute="_uom_exist", store=True)
    uom_category_id = fields.Many2one('uom.category', string='Uom Category', related="uom_id.category_id", store=False)

    @api.depends('product_uom_line_ids.uom_id')
    def _uom_exist(self):
        for product in self:
            product.uom_exist_ids = [
                (6, 0, product.product_uom_line_ids.uom_id.ids)
            ] if product.product_uom_line_ids else False


class ProductUomLine(models.Model):
    _name = 'product.uom.line'
    _description = "Product UoM Line"

    name = fields.Char(string='Name')
    uom_id = fields.Many2one('uom.uom', string='UoM', required=False)
    conversion = fields.Float(string='Conversion')
    product_tmpl_id = fields.Many2one('product.template', string='Product')


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"
    _order = 'sequence, date desc, min_qty DESC, price, id'

    product_uom = fields.Many2one(related='product_tmpl_id.uom_id')
    date = fields.Date(
        string='Date', 
        required=False)
