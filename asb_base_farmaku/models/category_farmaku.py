from odoo import models, fields, api

class CategoryFarmaku(models.Model):
    _name = 'category.farmaku'
    _description = 'Category Farmaku'

    name = fields.Char(string='Name')
    icon_url_path = fields.Char(string='Icon Url Path')
    image_url_path = fields.Char(string='Image Url Path')
    is_show_homepage = fields.Boolean(string='Show Homepage')
    category_key = fields.Char(string='Category Key')
    meta_description = fields.Char(string='Meta Description')
    meta_keyword = fields.Char(string='Meta Keyword')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')

class ProductCategoryFarmaku(models.Model):
    _name = 'product.category.farmaku'
    _description = 'Product Category Farmaku'

    product_id = fields.Many2one('product.product', string='Product')
    category_id = fields.Many2one('category.farmaku', string='Category')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')