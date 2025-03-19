# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_enable_order_signature = fields.Boolean(
        string="Allow Signature")
    sh_enable_name = fields.Boolean(string="Allow Name With Signature")
    sh_enable_date = fields.Boolean(string="Allow Date With Signature")
    sh_display_signature_detail = fields.Boolean(
        string="Display Signature Detail In Receipt")
    sh_display_signature = fields.Boolean(
        string="Display Signature In Receipt")
    sh_display_name = fields.Boolean(string="Display Name In Receipt")
    sh_display_date = fields.Boolean(string="Display Date In Receipt")


class pos_order(models.Model):
    _inherit = "pos.order"

    signature = fields.Binary(string="Signature")
    signature_name = fields.Char(string="Name : ")
    signature_date = fields.Date(string="Date : ")

    def _order_fields(self, ui_order):
        res = super(pos_order, self)._order_fields(ui_order)
#         res['signature'] = ui_order.get('signature', False)
        res.update({
            'signature': ui_order.get('signature')[1] if ui_order.get('signature') else False,
            'signature_name': ui_order.get('signature_name') or False,
            'signature_date': ui_order.get('signature_date') or False
        })
        return res
