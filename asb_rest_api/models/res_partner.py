from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    gender = fields.Char(string='Gender')
    date_of_birth = fields.Datetime(string='Date Of Birth')
    farmaku_customer_id = fields.Integer(string='Farmaku Customer ID')
