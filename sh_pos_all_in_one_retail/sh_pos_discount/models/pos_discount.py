# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import fields, models


class PosDiscount(models.Model):
    _name = 'pos.discount'
    _description = 'POS Discount'

    sh_discount_name = fields.Char("Name")
    sh_discount_code = fields.Char("Code")
    sh_discount_value = fields.Float("Value(%)")


class PosConfig(models.Model):
    _inherit = 'pos.config'

    # sh_apply_custom_discount = fields.Boolean(
        # string="Apply Custom Discount Using Standard Discount Button ")
    sh_apply_both_discount = fields.Boolean(string="Custom Discount Icon on Cart Line")


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    sh_discount_code = fields.Char('Discount Code')
