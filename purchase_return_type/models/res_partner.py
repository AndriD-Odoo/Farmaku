from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    purchase_return_type_id = fields.Many2one(
        comodel_name='purchase.return.type',
        string='Default Purchase Return Type',
        required=False)
