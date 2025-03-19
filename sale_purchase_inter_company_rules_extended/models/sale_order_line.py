from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    intercompany_purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='Intercompany Purchase Line',
        copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            if rec.sudo().order_id.auto_purchase_order_id and not self.env.context.get('force_create'):
                raise ValidationError(_(f'You can not add sale order line that came from intercompany transaction. '
                                        f'Ref: {rec.sudo().order_id.auto_purchase_order_id.name}'))
        return res

    def unlink(self):
        for rec in self:
            if rec.sudo().order_id.auto_purchase_order_id and not self.env.context.get('force_delete'):
                raise ValidationError(_(f'You can not delete sale order line that came from intercompany transaction. '
                                        f'Ref: {rec.sudo().order_id.auto_purchase_order_id.name}'))
        res = super().unlink()
        return res

    def write(self, values):
        res = super(SaleOrderLine, self).write(values)
        if 'product_uom_qty' in values:
            for rec in self:
                for move_id in rec.move_ids.filtered(lambda m: m.state not in ['done', 'cancel']):
                    uom_qty = rec.product_uom._compute_quantity(rec.product_uom_qty, rec.product_id.uom_id)
                    move_id.write({
                        'product_uom_qty': uom_qty,
                    })
                    for move_orig_id in move_id.move_orig_ids.filtered(lambda m: m.state not in ['done', 'cancel']):
                        total_qty = 0
                        for line in rec.order_id.order_line.filtered(lambda l: l.product_id.id == rec.product_id.id):
                            total_qty += line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
                        move_orig_id.write({
                            'product_uom_qty': total_qty,
                        })
        return res
