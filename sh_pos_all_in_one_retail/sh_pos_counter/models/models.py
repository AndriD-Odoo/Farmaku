# Copyright (C) Softhealer Technologies.

from odoo import fields, models, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_pos_item_counter = fields.Boolean("Enable Total Item Counter")
    enable_pos_qty_counter = fields.Boolean("Enable Total Qty Counter")
    enable_pos_item_report = fields.Boolean(
        "Display Total Item Counter On Pos Ticket")
    enable_pos_qty_report = fields.Boolean(
        "Display Total Qty Counter On Pos Ticket")


class PosOrder(models.Model):
    _inherit = 'pos.order'

    total_item = fields.Float(string="Total Items", readonly="1")
    total_qty = fields.Float(string="Total Qty", readonly="1")

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['total_item'] = ui_order.get('total_item', False)
        res['total_qty'] = ui_order.get('total_qty', False)
        return res
