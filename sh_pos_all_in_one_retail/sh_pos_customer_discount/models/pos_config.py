# Copyright (C) Softhealer Technologies.

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_enable_customer_discount = fields.Boolean(
        string='Enable Customer Discount')


class PosOrder(models.Model):
    _inherit = 'res.partner'

    sh_customer_discount = fields.Integer(string='POS Discount')
