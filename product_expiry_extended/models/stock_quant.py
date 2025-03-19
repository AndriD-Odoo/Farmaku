from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    expiration_date = fields.Datetime(
        related='lot_id.expiration_date', store=True, readonly=False
    )
    use_expiration_date = fields.Boolean(string='Use Expiration Date')
