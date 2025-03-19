# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_enable_auto_lock = fields.Boolean("Enable POS Auto Lock")
    sh_lock_timer = fields.Integer(string="Time Interval (In Second)")
