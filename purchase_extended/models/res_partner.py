from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    in_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string='Operation Type for Reordering Rule',
        required=False)
