from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'stock.picking'

    is_from_excel = fields.Boolean('From Marketplace', related='sale_id.is_from_excel')
    is_airwaybill_mkp = fields.Boolean(string='Need Airway Bill ?', related='sale_id.is_airwaybill_mkp')
    shop_name = fields.Char(related='sale_id.shop_name')
    period = fields.Char(related='sale_id.period')
    farmaku_order_mkp = fields.Char(string='Order ID (Marketplace)', related='sale_id.farmaku_order_mkp')
    invoice_mkp = fields.Char(related='sale_id.invoice_mkp')
    order_status_mkp = fields.Char(string='Order Status (Marketplace)', related='sale_id.order_status_mkp')
    
    airway_bill = fields.Char(string='Airway Bill')
    shipping_source = fields.Char(string='Shipping Data Source')
    shipping_price = fields.Float(string='Shipping Price + Fee', related='sale_id.shipping_price')
    shipping_insurance = fields.Float(string='Insurance', related='sale_id.shipping_insurance')
    shipping_price_total = fields.Float(string='Total Shipping Fee')

    recipient_name = fields.Char(string='Recipient (Marketplace)', related='sale_id.recipient_name')
    recipient_phone = fields.Char(string='Recipient Number (Marketplace)', related='sale_id.recipient_phone')
    recipient_address = fields.Char(string='Recipient Address (Marketplace)', related='sale_id.recipient_address')
