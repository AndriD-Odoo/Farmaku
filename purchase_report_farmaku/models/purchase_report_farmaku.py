# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PurchaseReportFarmaku(models.Model):
    _name = "purchase.report.farmaku"
    _description = "Purchase Report Farmaku"
    _order = 'id'

    @api.depends('price_unit', 'new_price_unit')
    def _get_diff(self):
        for rec in self:
            rec.price_diff = rec.new_price_unit - rec.price_unit

    @api.depends('purchase_line_id', 'new_purchase_line_id')
    def _get_price_unit(self):
        for rec in self:
            price_unit = 0
            new_price_unit = 0
            if rec.purchase_line_id:
                price_unit = rec.purchase_line_id.product_uom._compute_price(
                    rec.purchase_line_id.price_unit, rec.purchase_line_id.product_id.uom_po_id)
            if rec.new_purchase_line_id:
                new_price_unit = rec.new_purchase_line_id.product_uom._compute_price(
                    rec.new_purchase_line_id.price_unit, rec.new_purchase_line_id.product_id.uom_po_id)
            rec.price_unit = price_unit
            rec.new_price_unit = new_price_unit

    @api.depends('order_id', 'purchase_line_id', 'new_purchase_line_id')
    def _get_receipt_date(self):
        for rec in self:
            receipt_date = False
            new_receipt_date = False
            if rec.purchase_line_id:
                picking_ids = rec.purchase_line_id.mapped('move_ids.picking_id')
            else:
                picking_ids = rec.order_id.picking_ids
            picking_id = self.env['stock.picking'].search([
                ('id', 'in', picking_ids.ids),
                ('state', '=', 'done'),
            ], order='date_done asc', limit=1)
            if picking_id:
                receipt_date = picking_id.date_done
            new_picking_ids = rec.new_purchase_line_id.mapped('move_ids.picking_id')
            new_picking_id = self.env['stock.picking'].search([
                ('id', 'in', new_picking_ids.ids),
                ('state', '=', 'done'),
            ], order='date_done asc', limit=1)
            if new_picking_id:
                new_receipt_date = new_picking_id.date_done
            rec.receipt_date = receipt_date
            rec.new_receipt_date = new_receipt_date

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=False)
    order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='PO Reference',
        required=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
        domain=[('supplier_rank', '!=', 0)],
        store=True,
        related='order_id.partner_id')
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        store=True,
        related='order_id.picking_type_id.warehouse_id')
    representative_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Purchase Representative',
        store=True,
        related='order_id.user_id')
    create_date = fields.Datetime(
        string='Created Date',
        store=True,
        related='order_id.create_date')
    confirm_date = fields.Datetime(
        string='RFQ Confirmed Date',
        store=True)
    approve_date = fields.Datetime(
        string='RFQ Approved Date',
        store=True)
    receipt_date = fields.Datetime(
        string='PO Receipt Date',
        store=True,
        compute_sudo=True,
        compute='_get_receipt_date')
    type = fields.Selection(
        string='Type',
        selection=[
            ('tracking', 'Tracking'),
            ('change', 'Change'),
        ], required=True)
    purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='PO Line',
        required=False)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        related='purchase_line_id.product_id')
    price_unit = fields.Float(related='purchase_line_id.price_unit')
    new_purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='PO Line (Baru)',
        required=False)
    new_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='PO Reference (Baru)',
        related='new_purchase_line_id.order_id')
    new_create_date = fields.Datetime(
        string='Created Date (Baru)',
        related='new_purchase_line_id.order_id.create_date')
    new_receipt_date = fields.Datetime(
        string='Receipt Date (Baru)',
        compute_sudo=True,
        compute='_get_receipt_date')
    new_price_unit = fields.Float(
        string='Unit Price (Baru)',
        related='new_purchase_line_id.price_unit')
    new_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor (Baru)',
        related='purchase_line_id.order_id.partner_id')
    price_diff = fields.Float(
        string='Selisih',
        compute='_get_diff')

    def delete_existing(self, trx_type):
        self.env.cr.execute(f"""
            DELETE FROM
                purchase_report_farmaku
            WHERE
                user_id = {self.env.user.id}
                AND type = '{trx_type}'
        """)
