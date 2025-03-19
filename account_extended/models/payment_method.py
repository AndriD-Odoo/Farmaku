from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PaymentMethod(models.Model):
    _name = "payment.method"
    _description = "Payment Method"
    _order = "name"

    name = fields.Char(
        string='Payment Method',
        required=True)
