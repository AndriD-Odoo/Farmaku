from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _get_rendering_context(self, docids, data):
        res = super()._get_rendering_context(docids=docids, data=data)
        for id, external_id in self.get_external_id().items():
            if external_id in [
                'stock_extended.action_report_packing_list',
                'stock.action_report_delivery',
                'stock_extended.action_report_deliverylabel',
            ]:
                rec_ids = self.env['stock.picking'].browse(docids)
                for rec_id in rec_ids:
                    if not rec_id.box_lines:
                        raise ValidationError(_('Please input box first.'))
        return res
