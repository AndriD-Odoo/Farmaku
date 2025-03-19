# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_pos_logo = fields.Boolean("Enable POS Receipt Logo")
    receipt_logo = fields.Binary("Receipt Logo")
    sh_pos_header_logo = fields.Boolean("Enable POS Header Logo")
    header_logo = fields.Binary("Header Logo")


class ResCompany(models.Model):
    _inherit = 'res.company'

    sh_pos_global_logo = fields.Boolean("Enable POS Global Receipt Logo")
    global_receipt_logo = fields.Binary("Global Receipt Logo")
    sh_pos_global_header_logo = fields.Boolean("Enable POS Global Header Logo")
    global_header_logo = fields.Binary("Global Header Logo")


class ResConfigSettings(models.TransientModel,):
    _inherit = "res.config.settings"

    sh_pos_global_logo = fields.Boolean("Enable POS Global Receipt Logo", related='company_id.sh_pos_global_logo',
                                        readonly=False)
    global_receipt_logo = fields.Binary("Global Receipt Logo", related='company_id.global_receipt_logo',
                                        readonly=False)
    sh_pos_global_header_logo = fields.Boolean("Enable POS Global Header Logo", related='company_id.sh_pos_global_header_logo',
                                               readonly=False)
    global_header_logo = fields.Binary("Global Header Logo", related='company_id.global_header_logo',
                                       readonly=False)
