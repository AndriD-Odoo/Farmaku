from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    last_po_qty = fields.Float(
        string='Last PO Qty',
        required=False)
    min_qty = fields.Float(
        string='Min Qty')
