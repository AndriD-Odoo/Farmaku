import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('box_ids.lines')
    def _get_box_lines(self):
        for rec in self:
            rec.box_lines = rec.box_ids.mapped('lines')

    ip_address = fields.Char(
        string='Validator IP Address',
        copy=False)
    box_ids = fields.One2many(
        comodel_name='stock.picking.box',
        inverse_name='picking_id',
        string='Box',
        required=False)
    box_lines = fields.Many2many(
        comodel_name='stock.picking.box.line',
        compute='_get_box_lines')
    receiver_pic_id = fields.Many2one(
        comodel_name='res.partner',
        string='Receiver PIC',
        required=False)
    sender_pic_id = fields.Many2one(
        comodel_name='res.partner',
        string='Sender PIC',
        required=False)
    partner_contact_ids = fields.One2many(
        comodel_name='res.partner',
        related='partner_id.child_ids',
        string='Partner Contacts')
    warehouse_contact_ids = fields.One2many(
        comodel_name='res.partner',
        related='picking_type_id.warehouse_id.partner_id.child_ids',
        string='Warehouse Contacts')

    def _cron_rereserve_stock_pickings(self, warehouse_codes=[], limit=0):
        criteria = [
            ('state', 'in', ['partially_available', 'assigned']),
            ('location_id.usage', '=', 'internal'),
        ]
        if warehouse_codes:
            warehouse_ids = self.env['stock.warehouse'].search([
                ('code', 'in', warehouse_codes)
            ])
            view_location_ids = warehouse_ids.view_location_id
            location_ids = self.env['stock.location'].search([
                ('id', 'child_of', view_location_ids.ids)
            ])
            criteria += [
                ('location_id', 'in', location_ids.ids)
            ]
        picking_ids = self.search(criteria, limit=limit)
        total = len(picking_ids)
        current_index = 0
        for picking_id in picking_ids:
            current_index += 1
            picking_id.do_unreserve()
            picking_id.action_assign()
            _logger.info(f'\nProcess {current_index}/{total}')

    def _create_backorder(self):
        for picking in self:
            moves_to_backorder = picking.move_lines.filtered(lambda x: x.state not in ('done', 'cancel'))
            for move_id in moves_to_backorder:
                move_id.picking_id.message_post(body=_(
                    f'You have processed less products than the initial demand - {move_id.product_id.display_name}'
                ))
        res = super(StockPicking, self)._create_backorder()
        return res

    def button_validate(self):
        for rec in self:
            warehouse_ids = rec.location_id.get_warehouse() + rec.location_dest_id.get_warehouse()
            self.env.user.check_warehouse(warehouse_ids=warehouse_ids)
        res = super().button_validate()
        return res

    def _action_done(self):
        context = self.env.context.copy()
        context.update({
            'force_edit_sale': True
        })
        self = self.with_context(context)
        ip_address = request.httprequest.remote_addr
        for rec in self.filtered(lambda p: p.state not in ('done', 'cancel')):
            warehouse_ids = rec.location_id.get_warehouse() + rec.location_dest_id.get_warehouse()
            self.env.user.check_warehouse(warehouse_ids=warehouse_ids)
            rec.write({'ip_address': ip_address})
        res = super()._action_done()
        return res

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_(f'You can only delete draft transfer stock. {rec.display_name}'))
        res = super(StockPicking, self).unlink()
        return res

    def action_input_boxes(self):
        self.ensure_one()
        action = self.sudo().env.ref('stock_extended.stock_picking_box_action').read()[0]
        if self.box_ids:
            action['res_id'] = self.box_ids[0].id
        action['context'] = {
            'default_picking_id': self.id,
        }
        return action

    def write(self, values):
        res = super(StockPicking, self).write(values)
        if 'shipping_name' in values or 'shipping_service_name' in values:
            for rec in self:
                if rec.sale_id:
                    rec.sale_id.sudo().write({
                        'shipping_name': rec.shipping_name,
                        'shipping_service_name': rec.shipping_service_name,
                    })
        return res
