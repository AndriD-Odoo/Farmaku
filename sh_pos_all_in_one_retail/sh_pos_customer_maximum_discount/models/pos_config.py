# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import models, fields


class posCustomerInherit(models.Model):
    _inherit = 'res.partner'

    sh_enable_max_dic = fields.Boolean(string='Set maximum customer discount')
    sh_maximum_discount = fields.Float(string='Discount ')
    sh_discount_type = fields.Selection([('percentage', 'Percentage(%)'), (
        'fixed', 'Fixed')], string='Discount Type', default='percentage')


class PosConfigInherit(models.Model):
    _inherit = 'pos.config'

    sh_pos_enable_customer_max_discount = fields.Boolean(
        string='Enable Customer Maximum Discount')
