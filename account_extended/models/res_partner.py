import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _invoice_total(self):
        super()._invoice_total()
        for partner in self:
            domain = [
                ('partner_id', 'child_of', partner.ids),
                ('state', 'not in', ['draft', 'cancel']),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
            ]
            move_ids = self.env['account.move'].search(domain)
            partner.total_invoiced = sum(move_ids.mapped('amount_total'))

    def action_view_partner_invoices(self):
        action = super().action_view_partner_invoices()
        action['context'] = {'default_move_type': 'out_invoice', 'move_type': 'out_invoice',
                             'journal_type': 'sale', 'active_test': False, 'search_default_partner_id': self.id}
        return action

    def get_splitted_address(self):
        self.ensure_one()
        splitted_address = []
        if self.contact_address:
            splitted_address = self.contact_address.split('\n')
        _logger.info(f'\nsplitted_address: {splitted_address}')
        return splitted_address
