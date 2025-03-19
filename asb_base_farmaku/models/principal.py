from odoo import models, fields, api


class Principal(models.Model):
    _name = 'principal.principal'
    _description = 'Principal'

    name = fields.Char(string='Name')
    address = fields.Text(string='Address')
    address_note = fields.Text(string='Address Note')
    province = fields.Char(string='Province')
    city = fields.Char(string='City')
    district = fields.Char(string='District')
    zipcode = fields.Char(string='Zip Code')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')


class PrincipalPic(models.Model):
    _name = 'principal.pic'
    _description = 'Principal Pic'

    principal_id = fields.Many2one('principal.principal', string='Principal')
    pic_name = fields.Char(string='Pic Name')
    pic_phone = fields.Char(string='Pic Phone')
    pic_email = fields.Char(string='Pic Email')
    pic_title = fields.Char(string='Pic Title')
    pic_note = fields.Text(string='Pic Note')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')