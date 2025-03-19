from os import linesep
from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_from_excel = fields.Boolean(string='From Marketplace ?', default=False)
    is_airwaybill_mkp = fields.Boolean(string='Is Need Airway Bill ?', default=False)
    
    shop_name = fields.Char(string='Shop Name (Marketplace)', readonly=1)
    period = fields.Char(string='Periode (Marketplace)', readonly=1)
    farmaku_order_mkp = fields.Char(string='Order ID (Marketplace)', readonly=1)
    invoice_mkp = fields.Char(string='Invoice (Marketplace)')
    order_status_mkp = fields.Char(string='Order Status (Marketplace)', readonly=1)
    grand_total_price_mkp = fields.Float(string='Grand Total Price (Marketplace)')
    notes = fields.Html(string='Note')
    # notes_text = fields.Html(string='Note Text Only', compute='_get_text')
    
    shipping_name = fields.Char(string='Courier')
    shipping_service_name = fields.Char(string='Jenis Layanan')
    shipping_price = fields.Float(string='Shipping Price + Fee')
    shipping_insurance = fields.Float(string='Insurance')
    shipping_price_total = fields.Float(string='Total Shipping Fee')

    recipient_name = fields.Char(string='Recipient (Marketplace)')
    recipient_phone = fields.Char(string='Recipient Number (Marketplace)')
    recipient_address = fields.Char(string='Recipient Address (Marketplace)')

    def _get_text(self):
        for sale in self:
            sale.notes_text = sale.notes.get_text()

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'sale.order.line'
    
    product_id_mkp = fields.Char(string='Product ID (Marketplace)', readonly=True)
    is_from_excel = fields.Boolean(related='order_id.is_from_excel')
    sku = fields.Char(string='SKU', related="product_id.default_code", invisible=True)