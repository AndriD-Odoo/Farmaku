from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_uom_qty = fields.Float(digits='Product Unit of Measure Integer')
    quantity_done = fields.Float(digits='Product Unit of Measure Integer')
    reserved_availability = fields.Float(digits='Product Unit of Measure Integer')
    product_uom = fields.Many2one(string='UoM')

    def _send_stock_movement_report(self):
        exclude_warehouse_ids = []
        exclude_warehouse = self.env['ir.config_parameter'].sudo().get_param(
            'stock_extended.exclude_warehouse_daily_stock_movement')
        if exclude_warehouse:
            exclude_warehouse = exclude_warehouse.replace(' ', '').split(',')
            exclude_warehouse_ids = [int(warehouse_id) for warehouse_id in exclude_warehouse]
        user_ids = self.env['res.users'].sudo().search([
            ('property_warehouse_id', '!=', False),
            ('property_warehouse_id', 'not in', exclude_warehouse_ids),
        ])
        if user_ids:
            warehouse_ids = user_ids.mapped('property_warehouse_id')
            for warehouse_id in warehouse_ids:
                wizard_id = self.env['stock.movement.report.wizard'].create({
                    'warehouse_id': warehouse_id.id,
                })
                wizard_id.send_excel_report()

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        if vals.get('lot_id'):
            lot_id = self.env['stock.production.lot'].browse(vals['lot_id'])
            vals['expiration_date'] = lot_id.expiration_date
        return vals

    def write(self, values):
        res = super(StockMove, self).write(values)
        for move_id in self.filtered(lambda m: m.picking_id.picking_type_code == 'incoming'):
            if move_id.quantity_done > move_id.product_uom_qty:
                raise ValidationError(_(
                    f'Can not validate product {move_id.product_id.display_name} '
                    f'because done qty greater than demand qty.'
                ))
        return res

    @api.model
    def create(self, values):
        if values.get('picking_id'):
            picking_id = self.env['stock.picking'].browse(values['picking_id'])
            if picking_id.state != 'draft' and not self.env.context.get('default_pick_ids') and not self.env.context.get('force_add'):
                raise ValidationError(_('Can not add a move line not in draft status.'))
        res = super(StockMove, self).create(values)
        return res

    def _action_done(self, cancel_backorder=False):
        for rec in self:
            warehouse_ids = rec.location_id.get_warehouse() + rec.location_dest_id.get_warehouse()
            self.env.user.check_warehouse(warehouse_ids=warehouse_ids)
        res = super()._action_done(cancel_backorder=cancel_backorder)
        return res

    @api.constrains('product_uom_qty')
    def check_done_qty(self):
        for rec in self.filtered(lambda m: m.state not in ['done', 'cancel']):
            if rec.quantity_done > rec.product_uom_qty:
                raise ValidationError(_('Qty done cannot be greater than initial demand.'))
