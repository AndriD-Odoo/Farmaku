from odoo import models, fields, api


class Tag(models.Model):
    _name = 'tag.tag'
    _description = 'Tag'

    name = fields.Char(string='Name')
    image_url = fields.Char(string='Image Url')
    tag_link = fields.Char(string='Tag Link')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')


class TagProduct(models.Model):
    _name = 'tag.product'
    _description = 'Tag Product'

    product_id = fields.Many2one('product.product', string='Product')
    tag_id = fields.Many2one('tag.tag', string='Tag')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')


class TagPromo(models.Model):
    _name = 'tag.promo'
    _description = 'Tag Promo'

    tag_id = fields.Many2one('tag.tag', string='Tag')
    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')