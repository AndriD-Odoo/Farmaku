from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ElectronicDataCapture(models.Model):
    _name = "electronic.data.capture"
    _description = "Electronic Data Capture"
    _order = "name"

    name = fields.Char(
        string='EDC',
        required=True)
