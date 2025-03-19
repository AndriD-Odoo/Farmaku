from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil import tz


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    farmaku_ttb = fields.Datetime(string='TTB')

    def _prepare_invoice(self):
        def set_tz(date_convert, tz_from, tz_to):
            res = date_convert
            if date_convert:
                res = date_convert.replace(tzinfo=tz.gettz(tz_from))
                res = res.astimezone(tz.gettz(tz_to))
            return res
        res = super(PurchaseOrder, self)._prepare_invoice()
        for rec in self:
            if rec.farmaku_ttb:
                data = {
                    'purchase_order_link_id': rec.id,
                    'invoice_date': set_tz(rec.farmaku_ttb, 'UTC', rec.env.user.tz),
                    'date': set_tz(rec.farmaku_ttb, 'UTC', rec.env.user.tz)
                }
                res.update(data)
        return res

    def button_approve(self, force=False):
        res = super(PurchaseOrder, self).button_approve(force)
        for rec in self:
            if rec.farmaku_ttb:
                rec.write({'date_approve': rec.date_order})
        return res
