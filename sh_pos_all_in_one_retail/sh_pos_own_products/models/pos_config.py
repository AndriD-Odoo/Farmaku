# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import models, fields


class PosComfig(models.Model):
    _inherit = 'pos.config'

    sh_enable_own_product = fields.Boolean(string='Enable Own Product')


class PosProducts(models.Model):
    _inherit = 'product.product'

    sh_select_user = fields.Many2many(
        'res.users', 'pos_own_product_list', string='Allocate Sales Person')


class PosProductTmplate(models.Model):
    _inherit = 'product.template'

    sh_select_user = fields.Many2many(
        'res.users', related='product_variant_id.sh_select_user', string='Sale Person')
