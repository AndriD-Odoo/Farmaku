# Copyright (C) Softhealer Technologies.

from odoo import models, fields


class ProductInherit(models.Model):
    _inherit = 'product.template'

    sh_multiples_of_qty = fields.Char(string="Multiples of Quantity")


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_multi_qty_enable = fields.Boolean(
        string="Enable Product Multiple Quantity")
