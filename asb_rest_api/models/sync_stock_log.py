from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class SyncStockLog(models.Model):
    _name = "sync.stock.log"
    _description = "Sync Stock Log"
    _order = 'date desc'

    name = fields.Text('Detail')
    warehouse_code = fields.Char(
        string='Pharmacy Code',
        required=False)
    product_code = fields.Char(
        string='Product Code',
        required=False)
    qty = fields.Integer(
        string='Qty', 
        required=False)
    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now)
    action = fields.Char(
        string='Action', 
        required=False)

    def _cron_delete_log_more_than_30_days(self):
        date_30_days_ago = fields.Datetime.now() + timedelta(days=-30)
        log_ids = self.search([
            ('date', '<', date_30_days_ago),
        ])
        log_ids.unlink()
