from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil import tz


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    farmaku_real_order_id = fields.Char(string='Order ID Real Farmaku')
    farmaku_real_order_date = fields.Datetime(string='Order Date Real Farmaku')

    is_ready_to_confirm = fields.Boolean(string='Is Ready to Confirm ?')

    def compute_ready_confirm(self):
        for rec in self:
            if rec.order_line.filtered(lambda x: x._warehouse_product_quantity() == 0 and x.product_id.type != 'service'):
                rec.is_ready_to_confirm = False
            else:
                rec.is_ready_to_confirm = True

    def _prepare_invoice(self):
        def set_tz(date_convert, tz_from, tz_to):
            res = date_convert
            if date_convert:
                res = date_convert.replace(tzinfo=tz.gettz(tz_from))
                res = res.astimezone(tz.gettz(tz_to))
            return res
        res = super(SaleOrder, self)._prepare_invoice()
        for rec in self:
            if rec.farmaku_real_order_date:
                data = {
                    'sale_order_link_id': rec.id,
                    'invoice_date': set_tz(rec.farmaku_real_order_date, 'UTC', rec.env.user.tz),
                    'date': set_tz(rec.farmaku_real_order_date, 'UTC', rec.env.user.tz)
                } 
                res.update(data)
        return res

    def _prepare_confirmation_values(self):
        if self.farmaku_real_order_id:
            return {
                'state': 'sale',
                # 'date_order': fields.Datetime.now()
            }
        else:
            return {
                'state': 'sale',
                'date_order': fields.Datetime.now()
            }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _warehouse_product_quantity(self):
        warehouse_quantity = 0
        product_code = self.product_id.barcode
        warehouse_id = self.order_id.warehouse_id
        quant_ids = self.env['stock.quant'].sudo().search([
            '|', ('product_id.default_code','=', product_code),
            ('product_id.barcode','=', product_code),
            ('location_id.usage','=','internal'),
            ('location_id','=', warehouse_id.lot_stock_id.id)])
        warehouses = {}
        for quant in quant_ids:
            if quant.location_id:
                if quant.location_id not in warehouses:
                    warehouses.update({quant.location_id:0})
                warehouses[quant.location_id] += quant.available_quantity

        if warehouses:
            for location in warehouses:
                warehouse_quantity = warehouses[location]
        return warehouse_quantity


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        def set_tz(date_convert, tz_from, tz_to):
            res = date_convert
            if date_convert:
                res = date_convert.replace(tzinfo=tz.gettz(tz_from))
                res = res.astimezone(tz.gettz(tz_to))
            return res
        res = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)
        for rec in self:
            if order.farmaku_real_order_date:
                data = {
                    'sale_order_link_id': order.id,
                    'invoice_date': set_tz(order.farmaku_real_order_date, 'UTC', rec.env.user.tz),
                    'date': set_tz(order.farmaku_real_order_date, 'UTC', rec.env.user.tz)
                } 
                res.update(data)
        return res
