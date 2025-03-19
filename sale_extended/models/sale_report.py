from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleReport(models.Model):
    _inherit = 'sale.report'

    brand_id = fields.Many2one('product.brand', string='Brand')
    refund_status = fields.Selection(
        string='Refund Status',
        selection=[
            ('partial', 'Partial'),
            ('full', 'Fully Refund')
        ]
    )
    team_id = fields.Many2one(string='Sales Team ID')
    team_name = fields.Char(
        string='Sales Team',
    )
    order_id = fields.Many2one(string='Sale Order')
    pos_order_id = fields.Many2one(
        comodel_name='pos.order',
        string='POS Order',
        required=False)
    order_count = fields.Integer(
        string='Order #',
        default=0,
        required=False)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if 'order_id:count_distinct' not in fields:
            fields += ['order_id:count_distinct']
        if 'pos_order_id:count_distinct' not in fields:
            fields += ['pos_order_id:count_distinct']
        res = super(SaleReport, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )
        if isinstance(res, list):
            for r in res:
                if 'order_count' in r:
                    if isinstance(r.get('order_id', 0), int):
                        order_id_count = r.get('order_id', 0)
                    elif isinstance(r.get('order_id', 0), tuple):
                        order_id_count = 1
                    else:
                        order_id_count = 0
                    if isinstance(r.get('pos_order_id', 0), int):
                        pos_order_id_count = r.get('pos_order_id', 0)
                    elif isinstance(r.get('pos_order_id', 0), tuple):
                        pos_order_id_count = 1
                    else:
                        pos_order_id_count = 0
                    r['order_count'] = order_id_count + pos_order_id_count
        return res

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(SaleReport, self).fields_get(allfields, attributes=attributes)
        res['order_id']['selectable'] = True
        res['pos_order_id']['selectable'] = True
        return res

    def _query(self, with_clause="", fields=False, groupby="", from_clause=""):
        if not fields:
            fields = {}
        fields["brand_id"] = ", t.brand_id as brand_id"
        fields["refund_status"] = ", s.refund_status"
        fields["pos_order_id"] = ", NULL AS pos_order_id"
        # fields["order_count"] = ", 0 AS order_count"
        groupby += ", t.brand_id, s.refund_status"
        res = super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
        return res

    def _select_sale(self, fields=None):
        res = super()._select_sale(fields=fields)
        res += ' , ct.name AS team_name, 0 AS order_count '
        return res

    def _from_sale(self, from_clause=''):
        res = super()._from_sale(from_clause=from_clause)
        res += ' left join crm_team ct on (ct.id = s.team_id) '
        return res

    def _group_by_sale(self, groupby=''):
        res = super()._group_by_sale(groupby=groupby)
        res += ' , ct.name '
        return res

    def _select_pos(self, fields=None):
        res = super()._select_pos(fields=fields)
        res = res.replace('NULL AS warehouse_id', 'spt.warehouse_id AS warehouse_id')
        res = res.replace('NULL AS brand_id', 't.brand_id AS brand_id')
        res = res.replace('NULL AS pos_order_id', 'pos.id AS pos_order_id')
        res += ' , ct.name AS team_name, 0 AS order_count '
        return res

    def _from_pos(self):
        res = super()._from_pos()
        res += ''' 
            LEFT JOIN
                stock_picking_type spt ON (spt.id = config.picking_type_id)
        '''
        res += ' left join crm_team ct on (ct.id = pos.crm_team_id) '
        return res

    def _group_by_pos(self):
        res = super()._group_by_pos()
        res += '''
            , spt.warehouse_id,
            t.brand_id,
            pos.id,
            ct.name
        '''
        return res
