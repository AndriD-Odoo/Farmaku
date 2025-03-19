# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
import logging


class AccountMoveCustom(models.Model):
    _inherit = 'account.move'

    def action_upload_excel(self):
        ''' Open the account.upload.bank.recon wizard to upload data xlsx.
        :return: An action opening the account.upload.bank.recon.
        '''
        return {
            'name': 'Recon Bank Excel',
            'res_model': 'wizard.import.bank.excel',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }