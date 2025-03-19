from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseReturnType(models.Model):
    _name = "purchase.return.type"
    _description = "Purchase Return Type"

    name = fields.Char(
        string='Name',
        required=True)
