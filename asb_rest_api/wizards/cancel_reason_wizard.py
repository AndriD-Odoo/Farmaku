from odoo import fields, models, api, _
from odoo.exceptions import UserError


class CancelReasonWizard(models.TransientModel):
    _name = 'cancel.reason.wizard'
    _description = 'Cancel Reason Wizard'

    cancel_reason_id = fields.Many2one('cancel.reason', string='Cancel Reason')

    def proses_cancel(self):
        ids_to_change = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        doc_ids = self.env[active_model].browse(ids_to_change)
        return doc_ids.with_context(cancel_reason_id=self.cancel_reason_id).action_cancel()
