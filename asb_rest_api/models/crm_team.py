from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    code = fields.Char(
        string='Code',
        required=False)
