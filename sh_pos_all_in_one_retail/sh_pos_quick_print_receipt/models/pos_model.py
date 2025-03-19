# Copyright (C) Softhealer Technologies.

from odoo import models,fields

class PosConfig(models.Model):
    _inherit = "pos.config"
    
    sh_is_quick_receipt_print = fields.Boolean(string="Print Quick Receipt")
