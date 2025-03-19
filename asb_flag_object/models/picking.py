from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil import tz


class Picking(models.Model):
    _inherit = 'stock.picking'


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_order_link_id = fields.Many2one('sale.order', string='Sale Order ID')
    purchase_order_link_id = fields.Many2one('purchase.order', string='Purchase Order ID')

    def action_bulk_payment(self):
        for invoice in self:
            if invoice.state == 'posted':
                payment = invoice.env['account.payment.register'].with_context\
                    (active_model=invoice._name,active_ids=invoice.ids,dont_redirect_to_payments=True,default_payment_date=invoice.invoice_date)\
                        .create({}).action_create_payments()

    def _post(self, soft=True):
        def set_tz(date_convert, tz_from, tz_to):
            res = date_convert
            if date_convert:
                res = date_convert.replace(tzinfo=tz.gettz(tz_from))
                res = res.astimezone(tz.gettz(tz_to))
            return res
        for rec in self:
            if rec.stock_move_id.picking_id.purchase_id.farmaku_ttb:
                rec.write({'date': set_tz(rec.stock_move_id.picking_id.purchase_id.farmaku_ttb, 'UTC', rec.env.user.tz)})
            elif rec.stock_move_id.picking_id.sale_id.farmaku_real_order_date:
                rec.write({'date': set_tz(rec.stock_move_id.picking_id.sale_id.farmaku_real_order_date, 'UTC', rec.env.user.tz)})
            elif rec.sale_order_link_id:
                rec.write({'date': set_tz(rec.sale_order_link_id.farmaku_real_order_date, 'UTC', rec.env.user.tz)})
            elif rec.purchase_order_link_id:
                rec.write({'date': set_tz(rec.purchase_order_link_id.farmaku_ttb, 'UTC', rec.env.user.tz)})
        res = super(AccountMove, self)._post(soft)
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder)
        for rec in self:
            if rec.picking_id.purchase_id.farmaku_ttb:
                rec.write({'date': rec.picking_id.purchase_id.farmaku_ttb})
            elif rec.picking_id.sale_id.farmaku_real_order_date:
                rec.write({'date': rec.picking_id.sale_id.farmaku_real_order_date})
        return res


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _action_done(self):
        res = super(StockMoveLine, self)._action_done()
        for rec in self:
            try:
                if rec.picking_id.purchase_id.farmaku_ttb:
                    rec.write({'date': rec.picking_id.purchase_id.farmaku_ttb})
                elif rec.picking_id.sale_id.farmaku_real_order_date:
                    rec.write({'date': rec.picking_id.sale_id.farmaku_real_order_date})
            except:
                continue
        return res


class StockValuationLayer(models.Model):

    _inherit = 'stock.valuation.layer'

    def create(self, vals):
        res = super(StockValuationLayer, self).create(vals)
        for rec in res:
            if rec.stock_move_id.picking_id.sale_id.farmaku_real_order_date:
                date = rec.stock_move_id.picking_id.sale_id.farmaku_real_order_date
                query = """
                    UPDATE stock_valuation_layer SET
                        create_date = %s
                    WHERE id = %s
                """
                rec.env.cr.execute(query, [date, rec.id])
            elif rec.stock_move_id.picking_id.purchase_id.farmaku_ttb:
                date = rec.stock_move_id.picking_id.purchase_id.farmaku_ttb
                query = """
                UPDATE stock_valuation_layer SET
                        create_date = %s
                    WHERE id = %s
                """
                rec.env.cr.execute(query, [date, rec.id])
        return res
