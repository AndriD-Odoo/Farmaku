# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_enable_pos_product_price_confirm = fields.Many2one('res.groups', string='Allow Confirm Product Price.', compute='_compute_product_price_confirm_access')

    def _compute_product_price_confirm_access(self):
        for rec in self:
            rec.sh_enable_pos_product_price_confirm = self.env.ref('sh_pos_all_in_one_retail.group_pos_product_price')

