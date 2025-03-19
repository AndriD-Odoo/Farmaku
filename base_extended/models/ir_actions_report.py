from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _get_rendering_context(self, docids, data):
        res = super()._get_rendering_context(docids=docids, data=data)
        res['report_title'] = self.sudo().name or ''
        return res
