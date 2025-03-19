from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleReport(models.Model):
    _inherit = 'sale.report'

    cancel_reason_id = fields.Many2one('cancel.reason', string='Cancel Reason')

    def _query(self, with_clause="", fields=False, groupby="", from_clause=""):
        if not fields:
            fields = {}
        fields["cancel_reason_id"] = ", s.cancel_reason_id as cancel_reason_id"
        groupby += ", s.cancel_reason_id"
        res = super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
        return res

    def _group_by_sale(self, groupby=''):
        res = super()._group_by_sale(groupby=groupby)
        res += ' , s.cancel_reason_id '
        return res

    def _select_pos(self, fields=None):
        res = super()._select_pos(fields=fields)
        return res

    def _from_pos(self):
        res = super()._from_pos()
        return res

    def _group_by_pos(self):
        res = super()._group_by_pos()
        return res
