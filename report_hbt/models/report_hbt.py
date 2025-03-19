# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ReportHbt(models.Model):
    _name = "report.hbt"
    _description = "Report HBT"
    _order = 'id'

    @api.depends('line_id')
    def _get_cost(self):
        for rec in self:
            if rec.line_id.discount:
                cost = rec.line_id.price_unit - (rec.line_id.price_unit * rec.line_id.discount / 100)
            else:
                cost = rec.line_id.price_unit
            taxes_res = rec.line_id.taxes_id.compute_all(price_unit=cost, currency=rec.line_id.order_id.currency_id,
                                                         quantity=1, product=rec.line_id.product_id,
                                                         partner=rec.line_id.order_id.partner_id, is_refund=False,
                                                         handle_price_include=False)
            for tax in taxes_res.get('taxes', []):
                cost += tax['amount']
            if rec.line_id.product_uom != rec.line_id.product_id.uom_id:
                cost = rec.line_id.product_uom._compute_price(cost, rec.line_id.product_id.uom_id)
            rec.cost = cost

    @api.depends('uom_po_id')
    def _get_sale_price(self):
        for rec in self:
            rec.lst_price = rec.product_id.lst_price

    @api.depends('lst_price', 'cost')
    def _get_margin(self):
        for rec in self:
            rec.margin = rec.lst_price - rec.cost

    line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='PO Line',
        required=False)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=False)
    default_code = fields.Char(related='product_id.default_code', store=True)
    barcode = fields.Char(related='product_id.barcode', store=True)
    name = fields.Char(related='product_id.name', store=True, string='Product Name')
    brand_id = fields.Many2one(related='product_id.brand_id', store=True)
    categ_id = fields.Many2one(related='product_id.categ_id', store=True)
    uom_po_id = fields.Many2one(string='PO Unit of Measure', related='line_id.product_uom', store=True)
    factor_inv = fields.Float(string='Conversion', related='line_id.product_uom.factor_inv', store=True)
    cost = fields.Float(string='Cost', compute='_get_cost', store=True)
    discount = fields.Float(related='line_id.discount', store=True)
    lst_price = fields.Float(compute='_get_sale_price', store=True, string='Sales Price')
    margin = fields.Float(string='Margin', compute='_get_margin', store=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
        domain=[('supplier_rank', '!=', 0)],
        required=False)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=False)
    order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='PO Reference',
        required=False)
    exclude_from_tree = fields.Boolean(
        string='Exclude From Tree',
        required=False)

    def delete_existing(self):
        self.env.cr.execute(f"""
            DELETE FROM
                report_hbt
            WHERE
                user_id = {self.env.user.id}
        """)
