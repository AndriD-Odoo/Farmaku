# Copyright (C) Softhealer Technologies.

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_enable_prduct_code = fields.Boolean('Enable Product Internal Ref')
