# -*- coding: utf-8 -*-

from odoo import models, fields

class AccountMove(models.Model):
    _inherit = "account.move"

    settlement_batch_id = fields.Many2one('farmaku.settlement.batch', string='Settlement Batch', ondelete='set null')
    settlement_line_id = fields.Many2one('farmaku.settlement.line', string='Settlement Line', ondelete='set null')
