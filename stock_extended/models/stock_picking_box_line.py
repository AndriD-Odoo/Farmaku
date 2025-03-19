from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class StockPickingBoxLine(models.Model):
    _name = "stock.picking.box.line"
    _description = "Picking Box Line"

    @api.depends('item_details.qty')
    def _get_items(self):
        for rec in self:
            rec.item_count = len(rec.item_details)
            rec.qty = sum(rec.item_details.mapped('qty'))

    picking_box_id = fields.Many2one(
        comodel_name='stock.picking.box',
        string='Picking Box',
        required=False)
    item_details = fields.One2many(
        comodel_name='stock.picking.box.detail',
        inverse_name='line_id',
        string='Item Details',
        required=False)
    name = fields.Char(
        string='Box No',
        required=True)
    item_count = fields.Integer(
        string='Qty Items',
        compute='_get_items')
    qty = fields.Integer(
        string='Qty Units',
        compute='_get_items')

    @api.onchange('name')
    def onchange_fill_box_number(self):
        if not self.name:
            self.name = self.env['ir.sequence'].next_by_code('picking.box')

    @api.onchange('name')
    def onchange_fill_item_details(self):
        if not self.item_details:
            item_detail_vals = []
            used_move_line_dict = {}
            for detail_id in self.picking_box_id.lines.mapped('item_details'):
                used_move_line_dict[detail_id.move_line_id] = used_move_line_dict.get(
                    detail_id.move_line_id, 0) + detail_id.qty
            for move_line_id in self.picking_box_id.picking_id.move_line_ids:
                if move_line_id.state == 'done':
                    move_line_qty = move_line_id.qty_done
                else:
                    move_line_qty = move_line_id.product_uom_qty
                remaining_qty = move_line_qty - used_move_line_dict.get(move_line_id, 0)
                if remaining_qty > 0:
                    item_detail_vals.append((0, 0, {
                        'move_line_id': move_line_id.id,
                        'qty': remaining_qty,
                    }))
            self.item_details = item_detail_vals

    @api.model
    def create(self, values):
        res = super(StockPickingBoxLine, self).create(values)
        used_move_line_dict = {}
        for detail_id in res.picking_box_id.lines.mapped('item_details'):
            used_move_line_dict[detail_id.move_line_id] = used_move_line_dict.get(
                detail_id.move_line_id, 0) + detail_id.qty
        for move_line_id, qty in used_move_line_dict.items():
            if move_line_id.state == 'done':
                move_line_qty = move_line_id.qty_done
            else:
                move_line_qty = move_line_id.product_uom_qty
            if qty > move_line_qty:
                raise ValidationError(_(f'Qty product {move_line_id.product_id.name} '
                                        f'lot {move_line_id.lot_id.name} is over.'))
        return res

    def get_splitted_item_details(self):
        self.ensure_one()
        item_details = self.item_details
        splitted_item_details = []
        while item_details:
            current_item_details = item_details[:3]
            splitted_item_details.append(current_item_details)
            item_details -= current_item_details
        return splitted_item_details
