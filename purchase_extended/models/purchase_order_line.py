from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id,
                                                      product_qty, product_uom, company_id, values, po):
        res = super(PurchaseOrderLine, self).\
            _prepare_purchase_order_line_from_procurement(product_id, product_qty, product_uom, company_id, values, po)
        if product_uom.id != res['product_uom']:
            uom_po_id = self.env['uom.uom'].browse(res['product_uom'])
            price_unit = product_uom._compute_price(res['price_unit'], uom_po_id)
            res['price_unit'] = price_unit
        return res

    @api.depends('product_id', 'order_id.picking_type_id')
    def _get_stock(self):
        a_month_ago = datetime.now() - timedelta(days=30)
        a_month_ago = a_month_ago.strftime('%Y-%m-%d %H:%M:%S')
        for rec in self:
            current_stock_all_warehouse = []
            sale_qty = 0
            total_qty = 0
            warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', rec.company_id.id)], order='code')
            for warehouse_id in warehouse_ids:
                qty = rec.product_id.with_context({
                    'location': warehouse_id.lot_stock_id.id
                }).qty_available
                reserved_quants = self.env['stock.quant'].sudo().search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', 'child_of', warehouse_id.lot_stock_id.ids),
                    ('reserved_quantity', '>', 0),
                ])
                if reserved_quants:
                    qty -= sum(reserved_quants.mapped('reserved_quantity'))
                total_qty += qty
                current_stock_all_warehouse.append(f'{warehouse_id.code}: {round(qty)}')

                # sale_line_domain = [
                #     ('order_id.state', 'in', ['sale', 'done']),
                #     ('product_id', '=', rec.product_id.id),
                #     ('order_id.date_order', '<=', datetime.now()),
                #     ('order_id.date_order', '>=', a_month_ago),
                #     ('order_id.warehouse_id', '=', warehouse_id.id),
                # ]
                # pos_line_domain = [
                #     ('order_id.state', 'in', ['paid', 'done', 'invoiced']),
                #     ('product_id', '=', rec.product_id.id),
                #     ('order_id.date_order', '<=', datetime.now()),
                #     ('order_id.date_order', '>=', a_month_ago),
                #     ('order_id.session_id.config_id.picking_type_id.warehouse_id', '=', warehouse_id.id),
                # ]
                # sale_line_ids = self.env['sale.order.line'].search(sale_line_domain)
                # pos_line_ids = self.env['pos.order.line'].search(pos_line_domain)
                # for sale_line_id in sale_line_ids:
                #     sale_qty += sale_line_id.product_uom._compute_quantity(sale_line_id.product_uom_qty,
                #                                                            sale_line_id.product_id.uom_id)
                # for pos_line_id in pos_line_ids:
                #     sale_qty += pos_line_id.product_uom_id._compute_quantity(pos_line_id.qty,
                #                                                              pos_line_id.product_id.uom_id)
            qty_current_stock = 0
            current_warehouse_id = warehouse_ids.filtered(
                lambda l: l.lot_stock_id == rec.order_id.picking_type_id.default_location_dest_id)
            if current_warehouse_id:
                qty_current_stock = rec.product_id.with_context({
                    'location': current_warehouse_id[0].lot_stock_id.id
                }).qty_available
                reserved_quants2 = self.env['stock.quant'].sudo().search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', 'child_of', current_warehouse_id.lot_stock_id.ids),
                    ('reserved_quantity', '>', 0),
                ])
                if reserved_quants2:
                    qty_current_stock -= sum(reserved_quants2.mapped('reserved_quantity'))

            rec.current_stock_all_warehouse = '\n'.join(current_stock_all_warehouse)
            rec.day_30_sale = sale_qty
            rec.current_stock = f'{current_warehouse_id.code}: {round(qty_current_stock)} / {round(total_qty)}'

    @api.depends(
        'qty_received',
        'order_id.state',
        'invoice_lines',
    )
    def _is_price_unit_editable(self):
        for rec in self:
            is_price_unit_editable = True
            if rec.order_id.state not in ('draft', 'sent', 'to approve', 'purchase') or rec.qty_received or rec.invoice_lines:
                is_price_unit_editable = False
            rec.is_price_unit_editable = is_price_unit_editable

    current_stock = fields.Text(
        string='Current Stock',
        compute='_get_stock')
    current_stock_all_warehouse = fields.Text(
        string='Current Stock All Warehouse',
        compute='_get_stock')
    day_30_sale = fields.Float(
        string='S30D',
        digits='Product Unit of Measure Integer',
        compute='_get_stock')
    product_qty = fields.Float(digits='Product Unit of Measure Integer')
    qty_received = fields.Float(digits='Product Unit of Measure Integer')
    qty_invoiced = fields.Float(digits='Product Unit of Measure Integer')
    closed = fields.Boolean(
        string='Closed',
        copy=False)
    is_price_unit_editable = fields.Boolean(
        string='Is Price Unit Editable?',
        compute='_is_price_unit_editable')

    def _check_orderpoint_picking_type(self):
        if self.order_id.partner_id.in_type_id and self.order_id.partner_id.in_type_id != self.order_id.picking_type_id:
            raise ValidationError(
                _(f'Operation type {self.order_id.picking_type_id.display_name} '
                  f'is inconsistent with the vendor operation type {self.order_id.partner_id.in_type_id.display_name}')
            )
        elif not self.order_id.partner_id.in_type_id:
            super(PurchaseOrderLine, self)._check_orderpoint_picking_type()

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        # agar tidak mengambil location dari reordering rule
        if self.order_id.partner_id.in_type_id:
            res['location_dest_id'] = self.order_id._get_destination_location()
        return res

    def write(self, values):
        context = self.env.context.copy()
        context.update({
            'force_add': True
        })
        self = self.with_context(context)
        res = super(PurchaseOrderLine, self).write(values)
        if 'product_qty' in values:
            for rec in self:
                for move_id in rec.move_ids.filtered(lambda m: m.state not in ['done', 'cancel']):
                    uom_qty = rec.product_uom._compute_quantity(rec.product_qty, rec.product_id.uom_id)
                    move_id.write({
                        'product_uom_qty': uom_qty,
                    })
                    for move_dest_id in move_id.move_dest_ids.filtered(lambda m: m.state not in ['done', 'cancel']):
                        total_qty = 0
                        for line in rec.order_id.order_line.filtered(lambda l: l.product_id.id == rec.product_id.id):
                            total_qty += line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
                        move_dest_id.write({
                            'product_uom_qty': total_qty,
                        })
        return res

    @api.model_create_multi
    def create(self, vals_list):
        context = self.env.context.copy()
        context.update({
            'force_add': True
        })
        self = self.with_context(context)
        res = super(PurchaseOrderLine, self).create(vals_list)
        for r in res:
            if r.order_id.ttb_status:
                raise ValidationError(_(f'Can not add PO line {r.order_id.name} because has already been received.'))
        return res
