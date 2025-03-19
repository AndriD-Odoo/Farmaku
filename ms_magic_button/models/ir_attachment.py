from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    is_valid = fields.Boolean(
        string='Is Valid',
        default=False,
        copy=False)
