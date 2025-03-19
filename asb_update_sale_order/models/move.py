from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'Account Move'
    
    sale_id = fields.Many2one('sale.order', string='SO Document')
    is_from_excel = fields.Boolean(related='sale_id.is_from_excel')
    shop_name = fields.Char(related='sale_id.shop_name')
    period = fields.Char(related='sale_id.period')
    farmaku_order_mkp = fields.Char(related='sale_id.farmaku_order_mkp')
    invoice_mkp = fields.Char(related='sale_id.invoice_mkp')
