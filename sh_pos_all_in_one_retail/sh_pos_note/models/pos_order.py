# Copyright (C) Softhealer Technologies.
from odoo import fields, models, api


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    line_note = fields.Char('Line Note')


class PosOrder(models.Model):
    _inherit = 'pos.order'

    order_note = fields.Char('Order Note')

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['order_note'] = ui_order.get('order_note', False)
        return res
