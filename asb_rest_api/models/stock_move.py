from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    def sync_stock(self, with_destination=False):
        for rec in self:
            warehouse_id = rec.location_id.get_warehouse()
            if warehouse_id:
                location_ids = self.env['stock.location'].search([
                    ('id', 'child_of', warehouse_id.lot_stock_id.ids)
                ])
                if (rec.location_id.usage == 'internal' and warehouse_id.pharmacy_code
                        and rec.location_id.id in location_ids.ids):
                    rec.product_id._sync_update_stock(pharmacy_code=warehouse_id.pharmacy_code)
            warehouse_id = rec.location_dest_id.get_warehouse()
            if warehouse_id:
                location_dest_ids = self.env['stock.location'].search([
                    ('id', 'child_of', warehouse_id.lot_stock_id.ids)
                ])
                if with_destination and rec.location_id.id not in location_dest_ids.ids:
                    location_dest_ids = self.env['stock.location'].search([
                        ('id', 'child_of', warehouse_id.lot_stock_id.ids)
                    ])
                    if (rec.location_dest_id.usage == 'internal' and warehouse_id.pharmacy_code
                            and rec.location_dest_id.id in location_dest_ids.ids):
                        rec.product_id._sync_update_stock(pharmacy_code=warehouse_id.pharmacy_code)

    def _action_assign(self):
        res = super(StockMove, self)._action_assign()
        for rec in self:
            rec = rec.get_transaction_detail(action='reserve')
            rec.sync_stock()
        return res

    def _action_done(self, cancel_backorder=False):
        context = self.env.context.copy()
        context.update({
            'action': 'done'
        })
        self = self.with_context(context)
        move_ids = self.env['stock.move']
        for rec in self:
            if (((cancel_backorder and any(move_id.quantity_done for move_id in rec.picking_id.move_ids_without_package)
                    and rec.quantity_done < rec.product_uom_qty)) or rec.location_dest_id.usage == 'internal')\
                    or (rec.state != 'assigned'):
                move_ids += rec
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        for rec in move_ids.exists():
            rec = rec.get_transaction_detail(action='done')
            rec.sync_stock(with_destination=True)
        return res

    def _do_unreserve(self):
        res = super(StockMove, self)._do_unreserve()
        for rec in self:
            if self.env.context.get('action') != 'done':
                rec = rec.get_transaction_detail(action='unreserve')
                rec.sync_stock()
        return res

    def get_transaction_detail(self, action):
        context = self.env.context.copy()
        source_document = []
        picking_number = []
        reference = []
        for rec in self:
            origin = rec.picking_id.origin or rec.origin
            if origin and origin not in source_document:
                source_document.append(origin)
            if rec.picking_id and rec.picking_id.name not in picking_number:
                picking_number.append(rec.picking_id.name)
            if rec.reference:
                reference.append(rec.reference)
        context.update({
            'action': action,
            'source_document': ', '.join(source_document),
            'picking_number': ', '.join(picking_number),
            'reference': ', '.join(reference),
        })
        self = self.with_context(context)
        return self
