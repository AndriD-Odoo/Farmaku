# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import fields, models

class Posconfig(models.Model):
    _inherit = 'pos.config'

    # sh_allow_order_line_discount = fields.Boolean("Allow Line Discount")
    enable_custom_discount = fields.Boolean(string='Enable Custom Discount')
    sh_line_discount_or_custom_discount = fields.Selection([('line_discount', 'Simple Line Discount'), ('custom_discount', 'Custom Discount')], default='line_discount', string='Standard Discount Type')
    sh_allow_global_discount = fields.Boolean("Allow Global Discount")
