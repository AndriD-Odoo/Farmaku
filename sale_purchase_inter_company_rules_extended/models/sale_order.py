from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        for rec in self:
            if rec.sudo().auto_purchase_order_id and not self.env.context.get('force_confirm'):
                raise ValidationError(_(f'You can not confirm sale order that came from intercompany transaction. '
                                        f'Ref: {rec.sudo().auto_purchase_order_id.name}'))
        return res

    def action_cancel(self):
        res = super().action_cancel()
        for rec in self:
            if rec.sudo().auto_purchase_order_id and not self.env.context.get('force_cancel'):
                raise ValidationError(_(f'You can not cancel sale order that came from intercompany transaction. '
                                        f'Ref: {rec.sudo().auto_purchase_order_id.name}'))
        return res

    def write(self, values):
        res = super().write(values)
        for rec in self:
            if 'payment_term_id' in values:
                if rec.sudo().auto_purchase_order_id and not self.env.context.get('force_edit'):
                    raise ValidationError(_(f'You can not modify payment term that came from intercompany transaction. '
                                            f'Ref: {rec.sudo().auto_purchase_order_id.name}'))
        return res
