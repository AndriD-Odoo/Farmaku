from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.depends('name', 'state', 'created_purchase_line_id', 'move_orig_ids.state')
    def _get_purchase_order(self):
        for rec in self:
            created_purchase_id = self.env['purchase.order']
            if rec.created_purchase_line_id:
                created_purchase_id = rec.created_purchase_line_id.order_id
            elif rec.name and rec.location_id.usage == 'internal' and rec.location_dest_id.usage == 'internal':
                created_purchase_id = self.env['purchase.order'].search([
                    '|',
                    '|',
                    '|',
                    ('origin', '=', rec.name),
                    ('origin', 'like', f'%{rec.name}%'),
                    ('origin', 'like', f'{rec.name}%'),
                    ('origin', 'like', f'%{rec.name}'),
                ], limit=1)
            rec.created_purchase_id = created_purchase_id.id

    created_purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        compute='_get_purchase_order',
        store=True)
    uom_po_id = fields.Many2one(related='product_id.uom_po_id', string='UoM PO')
