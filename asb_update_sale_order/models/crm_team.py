from odoo import models, fields, api, _


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    shop_name = fields.Char(string='Shop Name')
