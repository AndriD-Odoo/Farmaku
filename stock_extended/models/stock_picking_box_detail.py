from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class StockPickingBoxDetail(models.Model):
    _name = "stock.picking.box.detail"
    _description = "Picking Box Detail"
    
    line_id = fields.Many2one(
        comodel_name='stock.picking.box.line',
        string='Picking Box Line',
        required=False)
    move_line_id = fields.Many2one(
        comodel_name='stock.move.line',
        string='Stock Move Line',
        required=False)
    barcode = fields.Char(
        string='Barcode',
        related='move_line_id.product_id.barcode')
    name = fields.Char(
        string='Product Name',
        related='move_line_id.product_id.name')
    qty = fields.Float(
        string='Qty',
        digits='Product Unit of Measure Integer')
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='UoM',
        related='move_line_id.product_uom_id')
    lot_name = fields.Char(
        string='Lot/SN',
        related='move_line_id.lot_id.name')
    expiration_date = fields.Datetime(
        string='Expired Date',
        related='move_line_id.expiration_date')
