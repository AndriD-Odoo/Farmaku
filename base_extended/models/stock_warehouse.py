import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    sia = fields.Char(
        string='SIA',
        required=False)
    apj_name = fields.Char(
        string='APJ Name',
        required=False)
    sipa = fields.Char(
        string='SIPA',
        required=False)
    digital_signature = fields.Binary(string="Digital Signature")

    def action_remove_signature(self):
        self.digital_signature = False
