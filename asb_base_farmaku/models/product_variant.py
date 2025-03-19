from odoo import models, fields, api

class ProductVariant(models.Model):
    _name = 'product.variant'
    _description = 'Product Variant'

    name = fields.Char(string='Name')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')

class ProductGroup(models.Model):
    _name = 'product.group'
    _description = 'Product Group'

    name = fields.Char(string='Name')
    product_variant1_id = fields.Many2one('product.variant', string='Product Variant 1')
    product_variant2_id = fields.Many2one('product.variant', string='Product Variant 2')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')
    
class ProductVariantGroup(models.Model):
    _name = 'product.variant.group'
    _description = 'Product Variant Group'

    product_id = fields.Many2one('product.product', string='Product')
    product_group_id = fields.Many2one('product.group', string='Product Group')
    product_variant_id = fields.Many2one('product.variant', string='Product Variant')
    alias = fields.Char(string='Alias')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')