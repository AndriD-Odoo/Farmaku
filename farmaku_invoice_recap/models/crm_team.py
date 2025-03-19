# -*- coding: utf-8 -*-

from odoo import models, fields

class CustomCRMTeam(models.Model):
    _inherit = 'crm.team'

    # Add your custom field to hold res.partner value
    partner_id = fields.Many2one('res.partner', string='Partner')
    team_code = fields.Char(string='Invoice Recap Code')
    payment_journal_id = fields.Many2one('account.journal', string='Payment Journal')

    # Add fields for dummy products
    gross_amount_product_id = fields.Many2one('product.product', string='Gross Amount Product')
    subsidy_amount_product_id = fields.Many2one('product.product', string='Subsidy Amount Product')
    shipping_cost_product_id = fields.Many2one('product.product', string='Shipping Cost Product')
    voucher_amount_product_id = fields.Many2one('product.product', string='Voucher Amount Product')
    commission_product_id = fields.Many2one('product.product', string='Commission Product')
    service_fee_product_id = fields.Many2one('product.product', string='Service Fee Product')

    # Add fields for account IDs
    gross_amount_account_id = fields.Many2one('account.account', string='Gross Amount Account')
    subsidy_amount_account_id = fields.Many2one('account.account', string='Subsidy Amount Account')
    shipping_cost_account_id = fields.Many2one('account.account', string='Shipping Cost Account')
    voucher_amount_account_id = fields.Many2one('account.account', string='Voucher Amount Account')
    commission_account_id = fields.Many2one('account.account', string='Commission Account')
    service_fee_account_id = fields.Many2one('account.account', string='Service Fee Account')