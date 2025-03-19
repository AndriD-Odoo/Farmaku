# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pro_min_sale_price = fields.Float(string="Minimum Sale Price")
    pro_max_sale_price = fields.Float(string="Maximum Sale Price")

    is_allow_to_set_price = fields.Boolean(compute = "compute_is_allow_to_set_price")

    def compute_is_allow_to_set_price(self):
        for rec in self:
            rec.is_allow_to_set_price = False
            if self.env.user.has_group('sh_pos_all_in_one_retail.group_set_price_in_product'):
                rec.is_allow_to_set_price = True