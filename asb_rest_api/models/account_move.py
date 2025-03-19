from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    order_number = fields.Char(string='Order Number', copy=False)
    payment_method = fields.Char(
        string='Payment Method Farmaku',
        copy=False,
        required=False)
    edc_id = fields.Many2one(
        comodel_name='electronic.data.capture',
        string='EDC',
        copy=False,
        required=False)
