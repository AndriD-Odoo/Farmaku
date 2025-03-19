from odoo import models, fields, api


class Ingredient(models.Model):
    _name = 'ingredient.ingredient'
    _description = 'Ingredient'

    name = fields.Char(string='Name')
    description = fields.Text(string='Description')
    article_url = fields.Char(string='Article Url')
    image_url_path = fields.Char(string='Image Url Path')

    active = fields.Boolean(string='Active', default=True) 
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')


class ProductIngredient(models.Model):
    _name = 'product.ingredient'
    _description = 'Product Ingredient'

    ingredient_id = fields.Many2one('ingredient.ingredient', string='Ingredient')
    product_id = fields.Many2one('product.product', string='Product')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')