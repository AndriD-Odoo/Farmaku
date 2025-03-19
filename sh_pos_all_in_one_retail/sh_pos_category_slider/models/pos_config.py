# Copyright (C) Softhealer Technologies.


from odoo import models, fields


class POsConfigInherit(models.Model):
    _inherit = 'pos.config'

    sh_enable_category_slider = fields.Boolean(string="Enable Pos Category slide")