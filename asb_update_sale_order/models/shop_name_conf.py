from odoo import models, fields, _

class ShopNameConf(models.Model):
    _name = 'shop.name.conf'
    _description = 'Mapping Shop Name'

    name = fields.Char(string='Nama Toko')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    