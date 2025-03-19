from odoo import fields, models, api, http, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('new_name')
    def _compute_name(self):
        for rec in self:
            if rec.new_name:
                rec.name = rec.new_name
            else:
                rec.name = 'New'

    new_name = fields.Char(
        string='New Name',
        copy=False)
    name = fields.Char(
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'journal_id' in vals:
                journal_id = self.env['account.journal'].sudo().search([
                    ('id', '=', vals['journal_id'])
                ])
                sequences = journal_id._get_sequence()
                sequence_id = sequences['original']
                refund_sequence_id = sequences['refund']
                if vals.get('move_type') in ['in_refund', 'out_refund']:
                    vals['new_name'] = refund_sequence_id.next_by_id()
                else:
                    vals['new_name'] = sequence_id.next_by_id()
        res = super().create(vals_list)
        for rec in res.filtered(lambda m: m.new_name == 'New' or not m.new_name):
            journal_id = rec.journal_id
            sequences = journal_id._get_sequence()
            sequence_id = sequences['original']
            refund_sequence_id = sequences['refund']
            if rec.move_type in ['in_refund', 'out_refund']:
                new_name = refund_sequence_id.next_by_id()
            else:
                new_name = sequence_id.next_by_id()
            rec.write({
                'new_name': new_name
            })
        return res

    def _onchange_journal(self):
        pass

    def _constrains_date_sequence(self):
        return False

    def _onchange_name_warning(self):
        pass
# trigger update
