# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class Product(models.Model):
    _inherit = 'product.product'

    is_rounding_product = fields.Boolean("Is Rounding Product ?")


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_enable_rounding = fields.Boolean("Enable Rounding")
    round_product_id = fields.Many2one('product.product', string="Rounding Product",
                                       domain=[('is_rounding_product', '=', True)])
    rounding_type = fields.Selection([('normal', 'Normal Rounding'), (
        'fifty', 'Rounding To Fifty')], string="Rounding Type", default='normal')