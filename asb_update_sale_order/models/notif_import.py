from odoo import models, fields, api, _

class NotifImport(models.Model):
    _name = 'notif.import'
    _description = 'notif.import'
    _rec_name = 'create_date'
    
    name = fields.Char(string='File Name', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', readonly=True)
    count_success = fields.Integer(string='Successfully Imported', readonly=True)
    count_fail = fields.Integer(string='Failed Imported', readonly=True)
    notif_import_line = fields.One2many('notif.import.line', 'notif_id', string='Notif Import Line')

    def delete_notif_import(self):
        return self.search([]).unlink()

class NotifImportLine(models.Model):
    _name = 'notif.import.line'
    _description = 'Notif Product Line'
    _rec_name = 'order'

    order = fields.Char(string='Order ID (Marketplace)')
    sku = fields.Char(string='Stock Keeping Unit (SKU)')
    product_name = fields.Char(string='Product Name')
    status = fields.Char(string='Status')
    reason = fields.Char(string='Reason')
    notif_id = fields.Many2one('notif.import', string='Notif Import')

    def delete_notif_import_line(self):
        return self.search([]).unlink()