# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_customer_order_history = fields.Boolean(
        string="Enable Customer Order History")
