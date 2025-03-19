from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        res = super()._prepare_sale_order_data(
            name=name,
            partner=partner,
            company=company,
            direct_delivery_address=direct_delivery_address
        )
        if self.sudo().picking_type_id.warehouse_id.partner_shipping_id:
            res['partner_shipping_id'] = self.sudo().picking_type_id.warehouse_id.partner_shipping_id.id
        res.update({
            'payment_term_id': self.payment_term_id.id,
            'user_id': self.user_id.id,
        })
        return res

    def button_confirm(self):
        res = super().button_confirm()
        for order in self:
            company_rec = self.env['res.company']._find_company_from_partner(order.partner_id.id)
            if company_rec and company_rec.rule_type in ('purchase', 'sale_purchase') and (not order.auto_generated):
                order.with_user(company_rec.intercompany_user_id).with_context(
                    default_company_id=company_rec.id).with_company(
                    company_rec).inter_company_create_sale_order(company_rec)
        return res

    def button_approve(self, force=False):
        res = super().button_approve()
        for rec in self:
            sale_order_id = self.env['sale.order'].sudo().search([
                ('auto_purchase_order_id', '=', rec.id),
                ('state', 'in', ['draft', 'sent']),
            ], limit=1)
            if sale_order_id:
                sale_order_id.with_context(force_confirm=True).action_confirm()
        return res

    def inter_company_create_sale_order(self, company):
        self = self.with_context({
            'force_confirm': True,
            'force_cancel': True,
            'force_create': True,
            'force_edit': True,
            'force_delete': True,
        })
        # skip jika sudah ada sale order sebelumnya
        purchase_ids = self.env['purchase.order']
        for rec in self:
            sale_order_id = self.env['sale.order'].sudo().search([
                ('auto_purchase_order_id', '=', rec.id),
                ('state', '!=', 'cancel'),
            ], limit=1)
            if sale_order_id:
                purchase_ids |= rec
        res = super(PurchaseOrder, self-purchase_ids).inter_company_create_sale_order(company=company)
        for rec in self:
            sale_order_id = self.env['sale.order'].sudo().search([
                ('auto_purchase_order_id', '=', rec.id),
                ('state', '!=', 'cancel'),
            ], limit=1)
            # selalu update vendor reference, default hanya diupdate jika kosong
            if sale_order_id and rec.partner_ref != sale_order_id.name:
                rec.partner_ref = sale_order_id.name
        return res

    def button_cancel(self):
        self = self.with_context({
            'force_confirm': True,
            'force_cancel': True,
            'force_create': True,
            'force_edit': True,
            'force_delete': True,
        })
        done_moves = self.env['stock.move']
        for rec in self:
            done_move_qty = 0
            return_done_move_qty = 0
            done_move_ids = rec.picking_ids.mapped('move_ids_without_package').filtered(
                lambda m: not m.origin_returned_move_id and m.state == 'done')
            return_move_ids = rec.picking_ids.mapped('move_ids_without_package').filtered(
                lambda m: m.origin_returned_move_id and m.state == 'done')
            for move_id in done_move_ids:
                done_move_qty += move_id.product_uom._compute_quantity(
                    move_id.product_uom_qty, move_id.product_id.uom_id)
            for move_id in return_move_ids:
                return_done_move_qty += move_id.product_uom._compute_quantity(
                    move_id.product_uom_qty, move_id.product_id.uom_id)
            if return_done_move_qty >= done_move_qty:
                done_move_ids.write({'state': 'cancel'})
                return_move_ids.write({'state': 'cancel'})
                done_moves |= done_move_ids
                done_moves |= return_move_ids
        res = super().button_cancel()
        if done_moves:
            done_moves.write({'state': 'done'})
        for rec in self:
            sale_order_id = self.env['sale.order'].sudo().search([
                ('auto_purchase_order_id', '=', rec.id),
                ('state', '!=', 'cancel'),
            ], limit=1)
            if sale_order_id:
                done_move_qty = 0
                return_done_move_qty = 0
                done_move_ids = sale_order_id.picking_ids.mapped('move_ids_without_package').filtered(
                    lambda m: not m.origin_returned_move_id and m.state == 'done')
                return_move_ids = sale_order_id.picking_ids.mapped('move_ids_without_package').filtered(
                    lambda m: m.origin_returned_move_id and m.state == 'done')
                for move_id in done_move_ids:
                    done_move_qty += move_id.product_uom._compute_quantity(
                        move_id.product_uom_qty, move_id.product_id.uom_id)
                for move_id in return_move_ids:
                    return_done_move_qty += move_id.product_uom._compute_quantity(
                        move_id.product_uom_qty, move_id.product_id.uom_id)
                if done_move_qty > return_done_move_qty:
                    raise ValidationError(_(f'Can not cancel PO. '
                                            f'Sale order {sale_order_id.name} has already been transferred.'))
                sale_order_id.action_cancel()
        return res

    @api.model
    def _prepare_sale_order_line_data(self, line, company):
        res = super()._prepare_sale_order_line_data(line=line, company=company)
        res.update({
            'product_uom_qty': line.product_qty,
            'product_uom': line.product_uom.id,
            'price_unit': line._get_intercompany_price_unit(),
            'discount': line.discount,
            'intercompany_purchase_line_id': line.id,
        })
        return res

    def write(self, values):
        self = self.with_context({
            'force_confirm': True,
            'force_cancel': True,
            'force_create': True,
            'force_edit': True,
            'force_delete': True,
        })
        res = super(PurchaseOrder, self).write(values)
        for rec in self:
            if 'payment_term_id' in values or 'user_id' in values:
                sale_order_id = self.env['sale.order'].sudo().search([
                    ('auto_purchase_order_id', '=', rec.id),
                    ('state', '!=', 'cancel'),
                ], limit=1)
                if sale_order_id:
                    sale_order_id.write({
                        'payment_term_id': rec.payment_term_id.id,
                        'user_id': rec.user_id.id,
                    })
        return res

    def sync_sale_order(self):
        self = self.with_context({
            'force_confirm': True,
            'force_cancel': True,
            'force_create': True,
            'force_edit': True,
            'force_delete': True,
        })
        for rec in self:
            sale_order_id = self.env['sale.order'].sudo().search([
                ('auto_purchase_order_id', '=', rec.id),
                ('state', '!=', 'cancel'),
            ], limit=1)
            if sale_order_id:
                product_ids = self.env['product.product']
                for line in rec.order_line.exists():
                    product_ids |= line.product_id
                    sale_line_id = self.env['purchase.order'].sudo().get_sale_line_id(
                        purchase_id=rec,
                        line=line
                    )
                    if sale_line_id:
                        sale_line_id.write({
                            'product_uom_qty': line.product_qty,
                            'product_uom': line.product_uom.id,
                            'discount': line.discount,
                            'price_unit': line._get_intercompany_price_unit(),
                        })
                    else:
                        company = self.env['res.company']._find_company_from_partner(rec.partner_id.id)
                        sale_line_data = rec._prepare_sale_order_line_data(line, company)
                        sale_line_data.update({
                            'order_id': sale_order_id.id
                        })
                        self.env['sale.order.line'].sudo().create(sale_line_data)
                sale_line_ids = self.env['sale.order.line'].sudo().search([
                    ('product_id', 'not in', product_ids.ids),
                    ('order_id', '=', sale_order_id.id),
                ])
                if sale_line_ids:
                    sale_line_ids.unlink()

    def get_sale_line_id(self, purchase_id, line):
        sale_line_id = self.env['sale.order.line'].sudo().search([
            ('intercompany_purchase_line_id', '=', line.id),
        ], limit=1)
        if not sale_line_id:
            sale_line_id = self.env['sale.order.line'].sudo().search([
                ('product_id', '=', line.product_id.id),
                ('order_id.auto_purchase_order_id', '=', purchase_id.id),
            ], limit=1)
        return sale_line_id
