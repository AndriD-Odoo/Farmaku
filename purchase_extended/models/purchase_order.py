from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.product_qty', 'order_line.qty_received')
    def _get_ttb_status(self):
        for rec in self:
            ttb_status = False
            ordered_qty = sum(rec.order_line.mapped('product_qty'))
            received_qty = sum(rec.order_line.mapped('qty_received'))
            _logger.info(f'\n ordered_qty {ordered_qty}, received_qty {received_qty}')
            if received_qty and received_qty >= ordered_qty:
                ttb_status = 'full'
            elif received_qty:
                ttb_status = 'partial'
            rec.ttb_status = ttb_status

    @api.depends('state')
    def _get_is_cancelable(self):
        for rec in self:
            is_cancelable = False
            if rec.state in ['draft', 'sent', 'to approve']:
                is_cancelable = True
            elif rec.state in ['purchase'] and self.env.user.has_group('purchase.group_purchase_manager'):
                is_cancelable = True
            rec.is_cancelable = is_cancelable

    ttb_status = fields.Selection(
        string='TTB Status',
        selection=[
            ('partial', 'Partially Receipt'),
            ('full', 'Fully Receipt'),
        ],
        compute='_get_ttb_status',
        store=True)
    sender_pic_id = fields.Many2one(
        comodel_name='res.partner',
        string='Sender PIC',
        required=False)
    receiver_pic_id = fields.Many2one(
        comodel_name='res.partner',
        string='Receiver PIC',
        required=False)
    partner_contact_ids = fields.One2many(
        comodel_name='res.partner',
        related='partner_id.child_ids',
        string='Vendor Contacts')
    warehouse_contact_ids = fields.One2many(
        comodel_name='res.partner',
        related='picking_type_id.warehouse_id.partner_id.child_ids',
        string='Warehouse Contacts')
    is_cancelable = fields.Boolean(
        string='Is Cancelable',
        compute='_get_is_cancelable')

    @api.onchange('partner_id')
    def onchange_sender_pic(self):
        self.sender_pic_id = False

    @api.onchange('picking_type_id')
    def onchange_receiver_pic(self):
        self.receiver_pic_id = False

    def _cron_auto_cancel(self, limit=0):
        a_month_ago = datetime.now() - timedelta(days=30)
        a_month_ago = a_month_ago.strftime('%Y-%m-%d %H:%M:%S')
        query = f"""
            SELECT 
                DISTINCT(po.id)
            FROM 
                purchase_order_line pol
            LEFT JOIN
                purchase_order po ON po.id = pol.order_id
            LEFT JOIN 
                (
                    SELECT
                        DISTINCT(purchase_line_id)
                    FROM
                        stock_move
                    WHERE
                        state NOT IN ('done', 'cancel')
                        AND purchase_line_id IS NOT NULL
                ) sm ON sm.purchase_line_id = pol.id
            WHERE 
                po.state != 'cancel'
                AND pol.product_id IS NOT NULL
                AND pol.closed IS NOT TRUE
                AND (
                    (po.date_approve <= '{a_month_ago}' AND po.state IN ('purchase', 'done'))
                    OR
                    (po.create_date <= '{a_month_ago}' AND po.state NOT IN ('purchase', 'done'))
                )
                AND (
                    po.state NOT IN ('purchase', 'done')
                    OR
                    (po.state IN ('purchase', 'done') AND sm.purchase_line_id IS NOT NULL)
                    OR
                    (po.state IN ('purchase', 'done') AND pol.qty_received < pol.product_qty)
                )
            ORDER BY
                po.id
        """
        if limit:
            query += f' LIMIT {limit} '
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()
        po_ids = []
        for res in result:
            po_ids.append(res['id'])
        if po_ids:
            order_ids = self.env['purchase.order'].browse(po_ids)
            total_order = len(order_ids)
            current_order = 1
            for order_id in order_ids:
                _logger.info(f'Process {current_order}/{total_order} ==> {order_id.name}')
                try:
                    if not any(pick.state == 'done' for pick in order_id.picking_ids):
                        order_id.button_cancel()
                    else:
                        line_ids = order_id.order_line.filtered(lambda l: not l.closed)
                        line_ids.write({'closed': True})
                    pick_ids = order_id.picking_ids.filtered(lambda p: p.state not in ['done', 'cancel'])
                    pick_ids.action_cancel()
                except Exception as e:
                    _logger.info('Error: %s' % e)
                current_order += 1

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        res['move_type'] = 'in_invoice'
        return res

    def _cron_purchase_vendor_revision(self, purchase_vendors=[]):
        partner_obj = self.env['res.partner'].sudo()
        queries = ''
        for purchase_number, from_to_vendor_ids in purchase_vendors.items():
            purchase_id = self.env['purchase.order'].sudo().search([
                ('name', '=', purchase_number)
            ], limit=1)
            if not purchase_id:
                continue
            for from_id, to_id in from_to_vendor_ids.items():
                vendor_from_id = partner_obj.search([('id', '=', from_id)])
                vendor_to_id = partner_obj.search([('id', '=', to_id)])
                if not vendor_from_id or not vendor_to_id:
                    continue
                queries += f"""
                    UPDATE
                        purchase_order
                    SET
                        partner_id = {to_id}
                    WHERE
                        id = {purchase_id.id}
                        AND partner_id = {from_id};
                """
                for picking_id in purchase_id.picking_ids:
                    queries += f"""
                        UPDATE
                            stock_picking
                        SET
                            partner_id = {to_id}
                        WHERE
                            id = {picking_id.id}
                            AND partner_id = {from_id};
                    """
                    for move_id in picking_id.move_ids_without_package:
                        queries += f"""
                            UPDATE
                                stock_move
                            SET
                                partner_id = {to_id}
                            WHERE
                                id = {move_id.id}
                                AND partner_id = {from_id};
                        """
                        for valuation_layer_id in move_id.stock_valuation_layer_ids:
                            queries += f"""
                                UPDATE
                                    account_move
                                SET
                                    partner_id = {to_id}
                                WHERE
                                    id = {valuation_layer_id.account_move_id.id}
                                    AND partner_id = {from_id};
                            """
                            for line_id in valuation_layer_id.account_move_id.line_ids:
                                queries += f"""
                                    UPDATE
                                        account_move_line
                                    SET
                                        partner_id = {to_id}
                                    WHERE
                                        id = {line_id.id}
                                        AND partner_id = {from_id};
                                """
                for invoice_id in purchase_id.invoice_ids:
                    queries += f"""
                        UPDATE
                            account_move
                        SET
                            partner_id = {to_id}
                        WHERE
                            id = {invoice_id.id}
                            AND partner_id = {from_id};
                    """
                    for invoice_line_id in invoice_id.line_ids:
                        queries += f"""
                            UPDATE
                                account_move_line
                            SET
                                partner_id = {to_id}
                            WHERE
                                id = {invoice_line_id.id}
                                AND partner_id = {from_id};
                        """
                    payment_ids = self.env['account.payment']
                    for partial, amount, counterpart_line in invoice_id._get_reconciled_invoices_partials():
                        payment_ids |= counterpart_line.move_id.payment_id
                    for payment_id in payment_ids:
                        queries += f"""
                            UPDATE
                                account_payment
                            SET
                                partner_id = {to_id}
                            WHERE
                                id = {payment_id.id}
                                AND partner_id = {from_id};
                        """
                        if payment_id.move_id:
                            queries += f"""
                                UPDATE
                                    account_move
                                SET
                                    partner_id = {to_id}
                                WHERE
                                    id = {payment_id.move_id.id}
                                    AND partner_id = {from_id};
                            """
                            for line_id in payment_id.move_id.line_ids:
                                queries += f"""
                                    UPDATE
                                        account_move_line
                                    SET
                                        partner_id = {to_id}
                                    WHERE
                                        id = {line_id.id}
                                        AND partner_id = {from_id};
                                """
        _logger.info(f'\n queries: {queries}')
        if queries:
            self.env.cr.execute(queries)
        # update vendor pricelist
        for purchase_number, from_to_vendor_ids in purchase_vendors.items():
            purchase_id = self.env['purchase.order'].sudo().search([
                ('name', '=', purchase_number)
            ], limit=1)
            if not purchase_id:
                continue
            purchase_id._add_supplier_to_product()

    def button_cancel(self):
        res = super(PurchaseOrder, self.filtered(lambda p: p.is_cancelable)).button_cancel()
        return res
