from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import pytz


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(pytz.timezone(self.env.user.tz or 'Asia/Jakarta'))

    def _send_near_expired_date(self):
        current_date = self.get_default_date_model()
        if current_date.day in (5, 20):
            wizard_id = self.env['near.expired.date.wizard'].create({})
            wizard_id.send_excel_report()

    def _update_expiration_date(self):
        warehouse_ids = self.env['stock.warehouse'].search([])
        for warehouse_id in warehouse_ids:
            location_ids = self.env['stock.location'].search([
                ('id', 'child_of', warehouse_id.lot_stock_id.ids)
            ])
            quant_ids = self.env['stock.quant'].search([
                ('location_id', 'in', location_ids.ids),
                ('lot_id', '!=', False),
            ])
            product_ids = quant_ids.mapped('product_id')
            for product_id in product_ids:
                current_quant_ids = quant_ids.filtered(lambda q: q.product_id.id == product_id.id)
                lot_ids = current_quant_ids.mapped('lot_id')
                last_purchase_move_line_id = self.env['stock.move.line'].search([
                    ('state', '=', 'done'),
                    ('product_id', '=', product_id.id),
                    ('location_id.usage', '=', 'supplier'),
                    ('location_dest_id', 'in', location_ids.ids),
                ], order='date desc', limit=1)
                if last_purchase_move_line_id:
                    expiration_date = last_purchase_move_line_id.date + timedelta(
                        days=last_purchase_move_line_id.product_id.expiration_time)
                    expiration_date_tz = pytz.UTC.localize(
                        expiration_date).astimezone(pytz.timezone(self.env.user.tz or 'Asia/Jakarta'))
                    expiration_date_str = fields.Datetime.to_string(expiration_date_tz)[:10]
                    if lot_ids:
                        self.env.cr.execute(f"""
                            UPDATE
                                stock_production_lot
                            SET
                                expiration_date = '{expiration_date_str}',
                                use_date = '{expiration_date_str}',
                                removal_date = '{expiration_date_str}',
                                alert_date = '{expiration_date_str}'
                            WHERE
                                id in {str(tuple(lot_ids.ids)).replace(',)', ')')};
                            UPDATE
                                stock_quant
                            SET
                                expiration_date = '{expiration_date_str}'
                            WHERE
                                id in {str(tuple(current_quant_ids.ids)).replace(',)', ')')};
                        """)
