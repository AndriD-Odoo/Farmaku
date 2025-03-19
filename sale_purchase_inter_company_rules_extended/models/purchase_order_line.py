from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _onchange_quantity(self):
        res = super()._onchange_quantity()
        if not self.product_id or self.invoice_lines or not self.company_id:
            return res
        # cek apakah transaksi intercompany atau bukan
        company_id = self.env['res.company'].sudo().search([
            ('partner_id', '=', self.partner_id.id)
        ], limit=1)
        all_company_ids = self.env['res.company'].sudo().search([])
        all_company_partner_ids = all_company_ids.mapped('partner_id')
        purchase_line_obj = self.env['purchase.order.line'].sudo()
        price_unit = 0
        po_line_uom = self.product_uom or self.product_id.uom_po_id
        if company_id:
            last_purchase_line_id = purchase_line_obj.search([
                ('product_id', '=', self.product_id.id),
                ('order_id.company_id', '=', company_id.id),
                ('order_id.state', 'in', ['purchase', 'done']),
            ], order='id desc', limit=1)
            if last_purchase_line_id:
                price_unit = last_purchase_line_id.price_unit
                if last_purchase_line_id.discount:
                    price_unit = price_unit * (1 - last_purchase_line_id.discount / 100)
                margin_percent = self.env['ir.config_parameter'].sudo().get_param(
                    'intercompany_price_margin_percent')
                try:
                    margin_percent = float(margin_percent)
                except Exception:
                    margin_percent = 0
                margin_amount = price_unit * margin_percent / 100
                price_unit = price_unit + margin_amount
            else:
                last_purchase_line_id = purchase_line_obj.search([
                    ('product_id', '=', self.product_id.id),
                    ('order_id.state', 'in', ['purchase', 'done']),
                    ('order_id.partner_id', 'not in', all_company_partner_ids.ids)
                ], order='id desc', limit=1)
                if last_purchase_line_id:
                    price_unit = last_purchase_line_id.price_unit
                    if last_purchase_line_id.discount:
                        price_unit = price_unit * (1 - last_purchase_line_id.discount / 100)
            price_unit = self.env['account.tax']._fix_tax_included_price_company(
                last_purchase_line_id.product_uom._compute_price(price_unit, po_line_uom),
                self.product_id.supplier_taxes_id,
                self.taxes_id,
                self.company_id,
            )
            if (price_unit and self.order_id.currency_id
                    and self.order_id.company_id.currency_id != self.order_id.currency_id):
                price_unit = self.order_id.company_id.currency_id._convert(
                    price_unit,
                    self.order_id.currency_id,
                    self.order_id.company_id,
                    self.date_order or fields.Date.today(),
                )
            self.price_unit = price_unit
        return res

    def write(self, values):
        for rec in self:
            if 'price_unit' in values and rec.price_unit != values.get('price_unit'):
                sale_line_id = self.env['purchase.order'].sudo().get_sale_line_id(
                    purchase_id=rec.order_id,
                    line=rec
                )
                done_move_id = self.env['stock.move'].sudo().search([
                    ('product_id', '=', sale_line_id.product_id.id),
                    ('state', '=', 'done'),
                    ('picking_id', 'in', sale_line_id.order_id.picking_ids.ids),
                ], limit=1)
                if sale_line_id.qty_delivered or done_move_id:
                    raise ValidationError(_(f'Can not change price unit product {rec.product_id.name} '
                                            f'because SO {sale_line_id.order_id.name} has already been delivered.'))
            if 'product_qty' in values and rec.product_qty != values.get('product_qty'):
                sale_line_id = self.env['purchase.order'].sudo().get_sale_line_id(
                    purchase_id=rec.order_id,
                    line=rec
                )
                done_move_id = self.env['stock.move'].sudo().search([
                    ('product_id', '=', sale_line_id.product_id.id),
                    ('state', '=', 'done'),
                    ('picking_id', 'in', sale_line_id.order_id.picking_ids.ids),
                ], limit=1)
                if sale_line_id.qty_delivered or done_move_id:
                    raise ValidationError(_(f'Can not change quantity product {rec.product_id.name} '
                                            f'because SO {sale_line_id.order_id.name} has already been delivered.'))
            if 'discount' in values and rec.discount != values.get('discount'):
                sale_line_id = self.env['purchase.order'].sudo().get_sale_line_id(
                    purchase_id=rec.order_id,
                    line=rec
                )
                done_move_id = self.env['stock.move'].sudo().search([
                    ('product_id', '=', sale_line_id.product_id.id),
                    ('state', '=', 'done'),
                    ('picking_id', 'in', sale_line_id.order_id.picking_ids.ids),
                ], limit=1)
                if sale_line_id.qty_delivered or done_move_id:
                    raise ValidationError(_(f'Can not change discount product {rec.product_id.name} '
                                            f'because SO {sale_line_id.order_id.name} has already been delivered.'))
        res = super(PurchaseOrderLine, self).write(values)
        for rec in self:
            if 'product_qty' in values or 'product_uom' in values or 'price_unit' in values or 'discount' in values:
                rec.order_id.sync_sale_order()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            rec.order_id.sync_sale_order()
        return res

    def unlink(self):
        order_ids = self.mapped('order_id')
        res = super().unlink()
        order_ids.exists().sync_sale_order()
        return res

    def _get_intercompany_price_unit(self):
        self.ensure_one()
        price_unit = self.price_unit
        if self.discount:
            price_unit = price_unit * (1 - self.discount / 100)
        if self.price_tax and self.product_qty:
            price_unit = price_unit + (self.price_tax / self.product_qty)
        return price_unit
