from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    opening_hours = fields.Float(string='Opening Hours')
    closing_hours = fields.Float(string='Closing Hours')