from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class StockPickingBox(models.Model):
    _name = "stock.picking.box"
    _description = "Picking Box"
    
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Reference',
        required=False)
    lines = fields.One2many(
        comodel_name='stock.picking.box.line',
        inverse_name='picking_box_id',
        string='Box Lines',
        required=False)
