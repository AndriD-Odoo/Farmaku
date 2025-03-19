from requests import exceptions
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class SyncPharmaciesWizard(models.TransientModel):
    _name = 'sync.pharmacies.wizard'
    _description = 'Synchronization Pharmacies'

    pharmacy_code = fields.Char(string='Pharmacy Code')
    item_per_page = fields.Integer(string='Item Perpage')
    page = fields.Integer(string='Page')
    product_ids = fields.Many2many(
        'product.product', 'wizard_sync_pharmacies_product_product',
        'wizard_id', 'product_id', 'Produk', copy=False)

    delimiter = fields.Char(string='Delimiter', default=',', size=1)
    row_start = fields.Integer(string='Row Start', default=1)
    worksheet_name = fields.Char(string='Worksheet Name')
    file = fields.Binary(string='File')
    filename = fields.Char(string='Filename')
    csv_format = fields.Char(string='Format', 
        default="[Pharmacy_Code],[Product_Code],[Barcode],[Product_Name],[UOM],[Unit_Price],[Stock]")
    search_product = fields.Char(string='Search')

    def get_product_wizard(self):
        url = self.env['ir.config_parameter'].sudo().get_param('farmaku_url')
        url_odoo = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if url == 'https://pharmacy-api.securerx.id' and url_odoo != 'https://farmaku.odoo.com':
            raise ValidationError(_('Url API Production Farmaku can use in Url Production Odoo'))
        return self.env.ref('asb_rest_api.pharmacies_product').report_action(self.ids, config=False)
    
    def get_product_report(self):
        data = {
            'search_product': self.search_product,
            'product_ids': self.product_ids,
            'pharmacy_code': self.pharmacy_code,
            'item_per_page': self.item_per_page,
            'page': self.page
        }
        return self.env['product.product']._sync_get_products(data)

    def update_stock_wizard(self):
        url = self.env['ir.config_parameter'].sudo().get_param('farmaku_url')
        url_odoo = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if url == 'https://pharmacy-api.securerx.id' and url_odoo != 'https://farmaku.odoo.com':
            raise ValidationError(_('Url API Production Farmaku can use in Url Production Odoo'))
        if self.product_ids :
            product_ids = self.product_ids
        else :
            product_ids = self.env['product.product'].search([])
        if not self.pharmacy_code :
            raise ValidationError(_('Please input pharmacy code.'))
        return product_ids.with_context({
            'manual_sync': True
        })._sync_update_stock(self.pharmacy_code)

    def update_price_wizard(self):
        url = self.env['ir.config_parameter'].sudo().get_param('farmaku_url')
        url_odoo = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if url == 'https://pharmacy-api.securerx.id' and url_odoo != 'https://farmaku.odoo.com':
            raise ValidationError(_('Url API Production Farmaku can use in Url Production Odoo'))
        return self.env['product.product']._sync_update_price(self.product_ids, self.pharmacy_code)
    
    def upload_product_wizard(self):
        url = self.env['ir.config_parameter'].sudo().get_param('farmaku_url')
        url_odoo = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if url == 'https://pharmacy-api.securerx.id' and url_odoo != 'https://farmaku.odoo.com':
            raise ValidationError(_('Url API Production Farmaku can use in Url Production Odoo'))
        data = {
            'csv_format': self.csv_format,
            'delimiter': self.delimiter,
            'row_start': self.row_start,
            'worksheet_name': self.worksheet_name,
            'file': self.file,
            'filename': self.filename
        }
        return self.env['product.product']._sync_upload_products(data)
    
    def get_cancel_reason(self):
        url = self.env['ir.config_parameter'].sudo().get_param('farmaku_url')
        url_odoo = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if url == 'https://pharmacy-api.securerx.id' and url_odoo != 'https://farmaku.odoo.com':
            raise ValidationError(_('Url API Production Farmaku can use in Url Production Odoo'))
        return self.env['cancel.reason'].sync_get_cancel_reason()
