# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

# Dashboard Sales Order Lines
class SOLinesDasboard(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sales Order line'

    # get value from another table

    get_sales_team = fields.Many2one(related='order_id.team_id', store=True, string='Sales Team')
    get_product_type_id = fields.Many2one(related='product_template_id.product_type_id', store=True, string='Product Type ID')
    order_id = fields.Many2one('sale.order', string='Order ID')
    get_refund_status = fields.Selection(
        related='order_id.refund_status', 
        string='Order Status', 
        store=True, 
        readonly=True
    )
    get_order_date = fields.Datetime(
        related='order_id.date_order', 
        string='Order Date', 
        store=True, 
        readonly=True
    )
    get_total_margin_persen = fields.Float(string="% Total Margin", compute="_compute_total_margin_percentile", store=True)
    
    @api.depends('total_margin', 'price_subtotal')
    # @api.depends('price_unit', 'price_subtotal')
    def _compute_total_margin_percentile(self):
       for record in self:
            record.get_total_margin_persen = (record.total_margin / record.price_subtotal) * 100
            # record.get_total_margin_persen = (record.price_unit / record.price_subtotal) * 100