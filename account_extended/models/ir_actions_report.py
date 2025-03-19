from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _get_rendering_context(self, docids, data):
        res = super()._get_rendering_context(docids=docids, data=data)
        if self.sudo().name == 'Commercial Invoice':
            move_id = self.env['account.move'].sudo().search([
                ('id', 'in', docids)
            ], limit=1)
            if move_id.move_type in ['in_refund', 'out_refund']:
                res['report_title'] = 'Credit Note'
        return res
