# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = "pos.config"

    def compute_access_rights(self):
        for rec in self:
            rec.allow_sh_pos_cancel = self.env.ref(
                'sh_pos_all_in_one_retail.group_sh_pos_cancel')

    allow_sh_pos_cancel = fields.Many2one(
        'res.groups', compute='compute_access_rights')


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def sh_fronted_cancel_draft(self, order_id):
        if order_id:
            return_data = []
            for each_order_id in order_id:
                order_obj = self.search([('id', '=', each_order_id)])
                if not order_obj:
                    order_obj = self.search([('sh_uid', '=', each_order_id)])
                cancel_delete = False
                cancel_draft = False

                if order_obj.company_id.pos_cancel_delivery:

                    if order_obj.picking_ids:
                        for picking in order_obj.picking_ids:
                            if picking.sudo().mapped('move_ids_without_package'):
                                picking.sudo().mapped('move_ids_without_package').sudo().write(
                                    {'state': 'draft'})
                                picking.sudo().mapped('move_ids_without_package').mapped(
                                    'move_line_ids').sudo().write({'state': 'draft'})
                                picking._sh_unreseve_qty()
#                                 picking.sudo().mapped('move_ids_without_package').mapped(
#                                     'move_line_ids').sudo().unlink()
#                                 picking.sudo().mapped('move_ids_without_package').sudo().unlink()
                            picking.sudo().write(
                                {'state': 'draft', 'show_mark_as_todo': True})
#                             picking.sudo().unlink()

                    elif not order_obj.picking_ids and order_obj.session_id:
                        pickings = self.env['stock.picking'].sudo().search(
                            [('pos_session_id', '=', order_obj.session_id.id)], limit=1)
                        if pickings:
                            for picking in pickings:
                                if picking.sudo().mapped('move_ids_without_package'):
                                    picking.sudo().mapped('move_ids_without_package').sudo().write(
                                        {'state': 'draft'})
                                    picking.sudo().mapped('move_ids_without_package').mapped(
                                        'move_line_ids').sudo().write({'state': 'draft'})
                                    picking._sh_unreseve_qty()
                                picking.sudo().write({'state': 'draft'})

                                for move_line in picking.move_ids_without_package:
                                    related_pos_line = order_obj.lines.filtered(
                                        lambda x: x.product_id == move_line.product_id)
                                    new_qty = move_line.product_uom_qty - related_pos_line.qty
                                    if new_qty == 0.0:
                                        move_line.mapped(
                                            'move_line_ids').sudo().unlink()
                                        move_line.sudo().unlink()
                                    else:
                                        move_line.mapped('move_line_ids').sudo().write(
                                            {'product_uom_qty': new_qty, 'qty_done': new_qty})
                                        move_line.sudo().write(
                                            {'product_uom_qty': new_qty, 'quantity_done': new_qty})

                                if picking.move_ids_without_package:
                                    picking.action_confirm()
                                    picking.action_assign()
                                    picking.button_validate()
                    cancel_draft = True
                if order_obj.company_id.pos_cancel_invoice:
                    order_obj.mapped('account_move').sudo().write(
                        {'state': 'draft'})
                    cancel_draft = True
                order_obj.sudo().write({'state': 'draft'})
                cancel_draft = True
                return_data.append({'sh_uid': order_id, 'order_id': self.id,
                                    'cancel_delete': cancel_delete, 'cancel_draft': cancel_draft})
            return return_data

    @api.model
    def sh_fronted_cancel_delete(self, order_id):
        if order_id:
            return_data = []
            for each_order_id in order_id:

                order_obj = 0
                order_obj = self.search([('id', '=', each_order_id)])
                if not order_obj:
                    order_obj = self.search([('sh_uid', '=', each_order_id)])
                
                cancel_delete = False
                cancel_draft = False

                if order_obj.company_id.pos_cancel_delivery:
                    if order_obj.picking_ids:
                        for picking in order_obj.picking_ids:
                            if picking.sudo().mapped('move_ids_without_package'):
                                picking.sudo().mapped('move_ids_without_package').sudo().write(
                                    {'state': 'draft'})
                                picking.sudo().mapped('move_ids_without_package').mapped(
                                    'move_line_ids').sudo().write({'state': 'draft'})
                                picking._sh_unreseve_qty()
                                picking.sudo().mapped('move_ids_without_package').mapped(
                                    'move_line_ids').sudo().unlink()
                                picking.sudo().mapped('move_ids_without_package').sudo().unlink()
                            picking.sudo().write(
                                {'state': 'draft', 'show_mark_as_todo': True})
                            picking.sudo().unlink()

                    elif not order_obj.picking_ids and order_obj.session_id:
                        pickings = self.env['stock.picking'].sudo().search(
                            [('pos_session_id', '=', self.session_id.id)], limit=1)
                        if pickings:
                            for picking in pickings:
                                if picking.sudo().mapped('move_ids_without_package'):
                                    picking.sudo().mapped('move_ids_without_package').sudo().write(
                                        {'state': 'draft'})
                                    picking.sudo().mapped('move_ids_without_package').mapped(
                                        'move_line_ids').sudo().write({'state': 'draft'})
                                    picking._sh_unreseve_qty()
                                picking.sudo().write({'state': 'draft'})

                                for move_line in picking.move_ids_without_package:
                                    related_pos_line = self.lines.filtered(
                                        lambda x: x.product_id == move_line.product_id)
                                    new_qty = move_line.product_uom_qty - related_pos_line.qty
                                    if new_qty == 0.0:
                                        move_line.mapped(
                                            'move_line_ids').sudo().unlink()
                                        move_line.sudo().unlink()
                                    else:

                                        move_line.mapped('move_line_ids').sudo().write(
                                            {'product_uom_qty': new_qty, 'qty_done': new_qty})
                                        move_line.sudo().write(
                                            {'product_uom_qty': new_qty, 'quantity_done': new_qty})

                                if picking.move_ids_without_package:
                                    picking.action_confirm()
                                    picking.action_assign()
                                    picking.button_validate()
                    cancel_delete = True

                if order_obj.company_id.pos_cancel_invoice:
                    order_obj.mapped('account_move').sudo().write(
                        {'state': 'draft', 'name': '/'})
                    order_obj.mapped('account_move').sudo().with_context(
                        {'force_delete': True}).unlink()
                    cancel_delete = True

                if order_obj.mapped('payment_ids'):
                    payment_ids = order_obj.mapped('payment_ids')
                    payment_ids.sudo().unlink()

                order_obj.sudo().write({'state': 'cancel'})
                order_obj.sudo().unlink()
                cancel_delete = True
                return_data.append({'sh_uid': order_id, 'order_id': order_obj.id,
                                    'cancel_delete': cancel_delete, 'cancel_draft': cancel_draft})
            return return_data

    @api.model
    def sh_fronted_cancel(self, order_id):
        if order_id:
            return_data = []
            for each_order_id in order_id:
                order_obj = self.search([('sh_uid', '=', each_order_id)])
                cancel_delete = False
                cancel_draft = False

                if order_obj.company_id.pos_cancel_delivery:
                    if order_obj.company_id.pos_operation_type == 'cancel_draft':
                        if order_obj.sudo().mapped('picking_id'):
                            if order_obj.sudo().mapped('picking_id').sudo().mapped('move_ids_without_package'):
                                order_obj.sudo().mapped('picking_id').sudo().mapped(
                                    'move_ids_without_package').sudo().write({'state': 'cancel'})
                                order_obj.sudo().mapped('picking_id').sudo().mapped('move_ids_without_package').mapped(
                                    'move_line_ids').sudo().write({'state': 'cancel'})
                            order_obj._sh_unreseve_qty()
                            order_obj.sudo().mapped('picking_id').sudo().write(
                                {'state': 'draft', 'show_mark_as_todo': True})
                            cancel_draft = True

                    elif order_obj.company_id.pos_operation_type == 'cancel_delete':
                        if order_obj.sudo().mapped('picking_id'):
                            if order_obj.sudo().mapped('picking_id').sudo().mapped('move_ids_without_package'):
                                order_obj.sudo().mapped('picking_id').sudo().mapped(
                                    'move_ids_without_package').sudo().write({'state': 'draft'})
                                order_obj.sudo().mapped('picking_id').sudo().mapped('move_ids_without_package').mapped(
                                    'move_line_ids').sudo().write({'state': 'draft'})
                                order_obj._sh_unreseve_qty()
                                order_obj.sudo().mapped('picking_id').sudo().mapped(
                                    'move_ids_without_package').sudo().unlink()
                                order_obj.sudo().mapped('picking_id').sudo().mapped(
                                    'move_ids_without_package').mapped('move_line_ids').sudo().unlink()

                            order_obj.sudo().mapped('picking_id').sudo().write(
                                {'state': 'draft'})
                            order_obj.sudo().mapped('picking_id').sudo().unlink()
                            cancel_delete = True

                if order_obj.company_id.pos_cancel_invoice:
                    if order_obj.mapped('invoice_id'):
                        if order_obj.mapped('invoice_id').mapped('move_id'):
                            move = order_obj.mapped(
                                'invoice_id').mapped('move_id')
                            move_line_ids = move.sudo().mapped('line_ids')

                            reconcile_ids = []
                            if move_line_ids:
                                reconcile_ids = move_line_ids.sudo().mapped('id')

                            reconcile_lines = order_obj.env['account.partial.reconcile'].sudo().search(
                                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                            if reconcile_lines:
                                reconcile_lines.sudo().unlink()

                            move.mapped(
                                'line_ids.analytic_line_ids').sudo().unlink()
                            move_line_ids.sudo().write(
                                {'parent_state': 'draft'})
                            move.sudo().write({'state': 'draft'})

                        if order_obj.company_id.pos_operation_type == 'cancel_draft':
                            order_obj.mapped('invoice_id').sudo().write(
                                {'state': 'draft'})
                            cancel_draft = True
                        elif order_obj.company_id.pos_operation_type == 'cancel_delete':
                            order_obj.mapped('invoice_id').sudo().write(
                                {'state': 'draft', 'move_name': ''})
                            order_obj.mapped('invoice_id').sudo().unlink()
                            cancel_delete = True

                if order_obj.mapped('statement_ids'):
                    statement_ids = order_obj.mapped('statement_ids')

                    journal_entry_ids = statement_ids.mapped(
                        'journal_entry_ids')
                    reconcile_ids = journal_entry_ids.sudo().mapped('id')

                    reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.sudo().unlink()

                    statement_ids.mapped('journal_entry_ids').mapped(
                        'move_id').write({'state': 'draft'})
                    statement_ids.mapped('journal_entry_ids').mapped(
                        'move_id').unlink()
                    statement_ids.mapped('journal_entry_ids').sudo().write(
                        {'state': 'draft'})
                    statement_ids.mapped('journal_entry_ids').sudo().unlink()

                if order_obj.company_id.pos_operation_type == 'cancel_draft':
                    order_obj.sudo().write({'state': 'draft'})
                    cancel_draft = True
                elif order_obj.company_id.pos_operation_type == 'cancel_delete':
                    order_obj.sudo().write({'state': 'cancel'})
                    order_obj.sudo().unlink()
                    cancel_delete = True
                return_data.append({'sh_uid': order_id, 'order_id': order_obj.id,
                                    'cancel_delete': cancel_delete, 'cancel_draft': cancel_draft})
            return return_data
