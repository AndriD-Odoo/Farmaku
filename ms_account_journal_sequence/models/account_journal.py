from odoo import fields, models, api, http, _
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string='Sequence',
        check_company=True,
        ondelete='cascade',
        required=False)
    refund_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string='Refund Sequence',
        check_company=True,
        ondelete='cascade',
        required=False)
    sequence = fields.Integer(string='Sequence Integer')

    @api.model_create_multi
    def create(self, vals_list):
        journal_ids = super().create(vals_list)
        for rec in journal_ids:
            rec._get_sequence()
        return journal_ids

    def write(self, vals):
        res = super(AccountJournal, self).write(vals)
        if 'code' in vals:
            for rec in self:
                rec._get_sequence()
        return res

    def _get_sequence(self):
        self.ensure_one()
        company_codes = {
            1: 'S',
            2: 'N',
            3: 'F',
        }
        sequence_obj = self.env['ir.sequence'].sudo()
        sequence_id = self.sequence_id
        refund_sequence_id = self.refund_sequence_id
        sequence_name = f'{self.code} Sequence'
        prefix_sequence_name = f'{self.code}{company_codes[self.company_id.id]}%(y)s%(month)s'
        refund_sequence_name = f'{self.code} Refund Sequence'
        prefix_refund_sequence_name = f'R{self.code}{company_codes[self.company_id.id]}%(y)s%(month)s'
        padding = 6
        if self.code in ['INV', 'STJ']:
            padding = 7
        if not sequence_id:
            sequence_id = sequence_obj.create({
                'name': sequence_name,
                'prefix': prefix_sequence_name,
                'padding': padding,
                'implementation': 'no_gap',
                'company_id': self.company_id.id,
            })
            self.sequence_id = sequence_id.id
        if sequence_id.name != sequence_name or sequence_id.prefix != prefix_sequence_name:
            sequence_id.write({
                'name': sequence_name,
                'prefix': prefix_sequence_name,
            })
        if not refund_sequence_id:
            refund_sequence_id = sequence_obj.create({
                'name': refund_sequence_name,
                'prefix': prefix_refund_sequence_name,
                'padding': padding,
                'implementation': 'no_gap',
                'company_id': self.company_id.id,
            })
            self.refund_sequence_id = refund_sequence_id.id
        if refund_sequence_id.name != refund_sequence_name or refund_sequence_id.prefix != prefix_refund_sequence_name:
            refund_sequence_id.write({
                'name': refund_sequence_name,
                'prefix': prefix_refund_sequence_name,
            })
        return {
            'original': sequence_id,
            'refund': refund_sequence_id,
        }

    def _generate_initial_sequence(self):
        bill_journal_ids = self.env['account.journal'].sudo().search([
            ('type', '=', 'purchase'),
            ('code', '!=', 'B'),
        ])
        bill_journal_ids.write({
            'code': 'B'
        })
        journal_ids = self.env['account.journal'].sudo().search([
            '|',
            ('sequence_id', '=', False),
            ('refund_sequence_id', '=', False),
        ])
        for journal_id in journal_ids:
            journal_id._get_sequence()
