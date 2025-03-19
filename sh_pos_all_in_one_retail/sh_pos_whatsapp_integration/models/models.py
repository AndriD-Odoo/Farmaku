# Copyright (C) Softhealer Technologies.
from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_whatsapp = fields.Boolean(string="Enable Whatsapp")


class ResUsers(models.Model):
    _inherit = "res.users"

    sign = fields.Text(string='Signature')
