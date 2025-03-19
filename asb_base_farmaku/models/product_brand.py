from odoo import models, fields, api

class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Product Brand'

    name = fields.Char(string='Name')
    icon_url_path = fields.Char(string='Icon Url Path')
    image_url_path = fields.Char(string='Image Url Path')
    is_show_homepage = fields.Boolean(string='Show Homepage')
    brand_key = fields.Char(string='Brand Key')
    meta_description = fields.Char(string='Meta Description')
    meta_keyword = fields.Char(string='Meta Keyword')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')


class ProductBrandPic(models.Model):
    _name = 'product.brand.pic'
    _description = 'Brand Pic'

    brand_id = fields.Many2one('product.brand', string='Brand')
    pic_name = fields.Char(string='Pic Name')
    pic_phone = fields.Char(string='Pic Phone')
    pic_email = fields.Char(string='Pic Email')
    pic_title = fields.Char(string='Pic Title')
    pic_note = fields.Text(string='Pic Note')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')