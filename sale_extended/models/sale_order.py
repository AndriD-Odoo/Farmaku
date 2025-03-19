from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends(
        'order_line.dpp_price',
        'order_line.product_uom_qty',
    )
    def _get_dpp_total(self):
        for rec in self:
            dpp_total = 0
            for line in rec.order_line:
                if line.product_uom_qty:
                    dpp_price = line.price_subtotal / line.product_uom_qty
                    dpp_price = dpp_price * 11 / 12
                    dpp_total += (dpp_price * line.product_uom_qty)
            rec.dpp_total = dpp_total

    is_backorder = fields.Boolean(
        string='Is Backorder?',
        copy=False)
    refund_status = fields.Selection(
        string='Refund Status',
        selection=[
            ('partial', 'Partial'),
            ('full', 'Fully Refund')
        ],
        copy=False
    )
    edc_id = fields.Many2one(
        comodel_name='electronic.data.capture',
        string='EDC',
        copy=False,
        required=False)
    dpp_total = fields.Monetary(
        string='DPP Total',
        compute_sudo=True,
        compute='_get_dpp_total')

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if 'search_default_partner_id' in self.env.context:
            args = [
                ['partner_id', 'child_of', self.env.context['search_default_partner_id']]
            ]
        res = super().search(args=args, offset=offset, limit=limit, order=order, count=count)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super().read_group(domain=domain, fields=fields, groupby=groupby,
                                 offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res

    def get_partner_bank_id(self):
        self.ensure_one()
        partner_bank_id = self.team_id.partner_bank_id.id
        team_partner_bank_id = self.env['crm.team.partner.bank'].search([
            ('team_id', '=', self.team_id.id),
            ('edc_id', '=', self.edc_id.id),
            ('payment_method_id.name', '=', self.payment_method),
        ], limit=1)
        if team_partner_bank_id:
            partner_bank_id = team_partner_bank_id.partner_bank_id.id
        return partner_bank_id

    def compute_refund_status(self):
        for rec in self:
            refund_status = False
            inv_refund = rec.invoice_ids.filtered(lambda r: r.move_type == 'out_refund' and r.state == 'posted')
            if inv_refund:
                total_refund = sum(refund.amount_total for refund in inv_refund)
                inv_ids = rec.invoice_ids.filtered(lambda r: r.move_type == 'out_invoice' and r.state == 'posted')
                total_inv = sum(inv.amount_total for inv in inv_ids)
                if total_refund >= total_inv:
                    refund_status = 'full'
                else:
                    refund_status = 'partial'
            rec.refund_status = refund_status

    def action_confirm(self):
        res = super().action_confirm()
        for rec in self:
            if not rec.is_backorder:
                picking_ids = rec.mapped('picking_ids').filtered(lambda pick: pick.state == 'confirmed')
                if picking_ids:
                    picking_ids.action_assign()
        return res

    def action_cancel(self):
        context = self.env.context.copy()
        context.update({'disable_cancel_warning': True})
        self = self.with_context(context)
        for rec in self:
            rec.return_picking()
            for invoice_id in rec.invoice_ids:
                if invoice_id.state == 'posted':
                    payment_ids = self.env['account.payment']
                    for partial, amount, counterpart_line in invoice_id._get_reconciled_invoices_partials():
                        payment_ids |= counterpart_line.move_id.payment_id
                    for payment_id in payment_ids:
                        if payment_id.state == 'posted':
                            payment_id.action_draft()
                        if payment_id.state == 'draft':
                            payment_id.action_cancel()
                    invoice_id.button_draft()
                if invoice_id.state == 'draft':
                    invoice_id.button_cancel()
        res = super().action_cancel()
        return res

    def return_picking(self):
        for rec in self.filtered(lambda s: s.state in ('sale', 'done')):
            picking_ids = self.env['stock.picking'].search([
                ('id', 'in', rec.picking_ids.ids),
            ], order='id desc')
            for picking_id in picking_ids:
                if any(move.origin_returned_move_id for move in picking_id.move_ids_without_package):
                    continue
                if any(move.returned_move_ids for move in picking_id.move_ids_without_package):
                    continue
                if picking_id.state not in ('done', 'cancel'):
                    picking_id.action_cancel()
                elif picking_id.state == 'done':
                    return_value = {
                        'picking_id': picking_id.id,
                        'location_id': picking_id.location_id.id,
                    }
                    picking_return_id = self.env['stock.return.picking'].create(return_value)
                    picking_return_id._onchange_picking_id()
                    if any(line.quantity for line in picking_return_id.product_return_moves):
                        new_picking_id, picking_type_id = picking_return_id._create_returns()
                        new_picking_id = self.env['stock.picking'].browse(new_picking_id)
                        for move_id in new_picking_id.move_lines:
                            origin_returned_move_id = move_id.origin_returned_move_id
                            move_id.move_line_ids.unlink()
                            for line in origin_returned_move_id.move_line_ids:
                                new_line_id = line.copy({
                                    'move_id': move_id.id,
                                    'picking_id': new_picking_id.id,
                                    'location_id': line.location_dest_id.id,
                                    'location_dest_id': line.location_id.id,
                                    'qty_done': line.qty_done,
                                })
                                if new_line_id.product_id.tracking != 'none' and not new_line_id.lot_id:
                                    quant_id = self.env['stock.quant'].sudo().search([
                                        ('product_id', '=', new_line_id.product_id.id),
                                        ('location_id', 'child_of', new_line_id.location_id.ids),
                                        ('lot_id', '!=', False),
                                    ], limit=1, order='reserved_quantity desc')
                                    lot_id = quant_id.lot_id
                                    if not lot_id and new_line_id.location_id.usage != 'internal':
                                        lot_id = self.env['stock.production.lot'].sudo().search([
                                            ('product_id', '=', new_line_id.product_id.id),
                                        ], limit=1, order='id desc')
                                    new_line_id.write({
                                        'lot_id': lot_id.id
                                    })
                        new_picking_id._action_done()

    def update_table(self, table_name, column_name, from_id, to_id, trx_ids=[], strict=False):
        if trx_ids:
            where_trx_ids = f' id in {str(tuple(trx_ids)).replace(",)", ")")} '
        else:
            where_trx_ids = ' 1=1 '
            if strict:
                return
        self.env.cr.execute(f"""
            UPDATE
                {table_name}
            SET
                {column_name} = {to_id}
            WHERE
                {column_name} = {from_id}
                AND {where_trx_ids}
        """)

    def force_change_customer(self, from_id, to_id):
        query = """
            SELECT 
                R.TABLE_NAME, r.column_name
            FROM 
                INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE u
            INNER JOIN 
                INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS FK ON U.CONSTRAINT_CATALOG = FK.UNIQUE_CONSTRAINT_CATALOG
                AND U.CONSTRAINT_SCHEMA = FK.UNIQUE_CONSTRAINT_SCHEMA
                AND U.CONSTRAINT_NAME = FK.UNIQUE_CONSTRAINT_NAME
            INNER JOIN 
                INFORMATION_SCHEMA.KEY_COLUMN_USAGE R ON R.CONSTRAINT_CATALOG = FK.CONSTRAINT_CATALOG
                AND R.CONSTRAINT_SCHEMA = FK.CONSTRAINT_SCHEMA
                AND R.CONSTRAINT_NAME = FK.CONSTRAINT_NAME
            WHERE 
                U.COLUMN_NAME = 'id'
                AND U.TABLE_NAME = 'res_partner'
            ORDER 
                BY R.TABLE_NAME asc
        """
        self.env.cr.execute(query=query)
        result = self.env.cr.dictfetchall()
        _logger.info(f'\n table list: {result}')
        for res in result:
            _logger.info(f'\n current table: {res["table_name"]} {res["column_name"]}')
            self.update_table(res['table_name'], res['column_name'], from_id, to_id)

    def customer_revision(self, sale_numbers=[], limit=0):
        for sale_number in sale_numbers:
            order_id = self.env['sale.order'].search([
                ('name', '=', sale_number)
            ])
            partner_id = self.env['res.partner'].search([
                ('mobile', '=', order_id.recipient_phone_web)
            ], limit=1)
            if not partner_id:
                if not order_id.recipient_phone_web:
                    continue
                product_pricelist_id = self.env['product.pricelist'].sudo().search([], limit=1)
                customer_result = {
                    'type': 'contact',
                    'company_type': 'person',
                    'customer_rank': 1,
                    'name': order_id.recipient_name_web,
                    'phone': order_id.recipient_phone_web,
                    'mobile': order_id.recipient_phone_web,
                    'gender': False,
                    'date_of_birth': False,
                    'street': order_id.recipient_address_web,
                    'city': False,
                    'country_id': self.env['res.country'].sudo().search([
                        ('code', '=', 'ID')
                    ]).id,
                    'zip': False,
                    'partner_longitude': False,
                    'partner_latitude': False,
                    'property_product_pricelist': product_pricelist_id.id,
                }
                partner_id = self.env['res.partner'].sudo().create(customer_result)
                partner_id._compute_display_name()
            self.update_table('stock_picking', 'partner_id', order_id.partner_id.id, partner_id.id, order_id.picking_ids.ids, strict=True)
            for picking_id in order_id.picking_ids:
                self.update_table('stock_move', 'partner_id', order_id.partner_id.id, partner_id.id, order_id.picking_ids.mapped('move_lines').ids, strict=True)
                account_move_ids = self.env['account.move'].search([
                    ('name', 'ilike', 'stj'),
                    ('ref', 'ilike', picking_id.name),
                    ('partner_id', '=', order_id.partner_id.id),
                ])
                self.update_table('account_move', 'partner_id', order_id.partner_id.id, partner_id.id, account_move_ids.ids, strict=True)
                account_move_line_ids = self.env['account.move.line'].search([
                    ('move_id.name', 'ilike', 'stj'),
                    ('name', 'ilike', picking_id.name),
                    ('partner_id', '=', order_id.partner_id.id),
                ])
                self.update_table('account_move_line', 'partner_id', order_id.partner_id.id, partner_id.id, account_move_line_ids.ids, strict=True)
            self.update_table('account_move', 'partner_id', order_id.partner_id.id, partner_id.id, order_id.invoice_ids.ids, strict=True)
            self.update_table('account_move', 'commercial_partner_id', order_id.partner_id.id, partner_id.id, order_id.invoice_ids.ids, strict=True)
            self.update_table('account_move', 'partner_shipping_id', order_id.partner_id.id, partner_id.id, order_id.invoice_ids.ids, strict=True)
            order_id.invoice_ids.invalidate_cache()
            order_id.invoice_ids._compute_invoice_partner_display_info()
            self.update_table('account_move_line', 'partner_id', order_id.partner_id.id, partner_id.id, order_id.invoice_ids.mapped('invoice_line_ids').ids, strict=True)
            self.update_table('account_move_line', 'partner_id', order_id.partner_id.id, partner_id.id, order_id.invoice_ids.mapped('line_ids').ids, strict=True)
            payment_ids = order_id.invoice_ids.mapped('line_ids.matched_debit_ids.debit_move_id.payment_id') + \
                order_id.invoice_ids.mapped('line_ids.matched_credit_ids.credit_move_id.payment_id')
            self.update_table('account_payment', 'partner_id', order_id.partner_id.id, partner_id.id, payment_ids.ids, strict=True)
            self.update_table('account_move', 'partner_id', order_id.partner_id.id, partner_id.id, payment_ids.mapped('move_id').ids, strict=True)
            self.update_table('account_move_line', 'partner_id', order_id.partner_id.id, partner_id.id, payment_ids.mapped('move_id.line_ids').ids, strict=True)
            self.update_table('sale_order', 'partner_id', order_id.partner_id.id, partner_id.id, order_id.ids, strict=True)
        if not sale_numbers:
            query = f"""
                SELECT
                    so.id
                FROM
                    sale_order so
                LEFT JOIN
                    res_partner rp ON rp.id = so.partner_id
                LEFT JOIN
                    crm_team ct ON ct.id = so.team_id
                WHERE
                    (so.recipient_phone_web IS NULL OR so.recipient_phone_web = '')
                    AND (rp.name IS NULL OR rp.name = '')
                    -- AND so.invoice_number ilike 'pos/%'
                    AND ct.code ilike 'farmaku%'
            """
            if limit:
                query += f' LIMIT {limit} '
            self.env.cr.execute(query=query)
            result = self.env.cr.dictfetchall()
            order_ids = []
            for res in result:
                order_ids.append(res['id'])
            order_ids = self.env['sale.order'].search([('id', 'in', order_ids)])
            _logger.info(f'\n order_ids: {order_ids.mapped("display_name")}')
            total_sales = len(order_ids)
            current_sale = 1
            for order_id in order_ids:
                _logger.info(f'Process sale {order_id.name} {current_sale}/{total_sales}')
                try:
                    order_id.force_change_customer(order_id.partner_id.id, order_id.warehouse_id.default_customer_id.id)
                    order_id.partner_id.unlink()
                except Exception:
                    pass
                current_sale += 1

    def discount_revision(self, sale_numbers):
        sale_ids = self.search([
            ('name', 'in', sale_numbers)
        ])
        total_sales = len(sale_ids)
        current_sale = 1
        for sale_id in sale_ids:
            _logger.info(f'Process update discount sale {sale_id.name} {current_sale}/{total_sales}')
            try:
                for invoice_id in sale_id.invoice_ids:
                    for inv_line_id in invoice_id.invoice_line_ids:
                        if inv_line_id.discount:
                            inv_line_id.write({
                                'discount': 0
                            })
                for line_id in sale_id.order_line:
                    if line_id.discount:
                        line_id.write({
                            'discount': 0
                        })
            except Exception as e:
                _logger.info(f'Discount revision error: {str(e)}')
            current_sale += 1

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({
            'warehouse_id': self.warehouse_id.id,
        })
        return invoice_vals

    def write(self, values):
        for rec in self:
            if 'state' not in values and not self.env.context.get('force_edit_sale') and rec.state in ['sale', 'done']:
                public_user_id = self.env.ref('base.public_user')
                if self.env.user.id != public_user_id.id and not self.env.user.has_group('sales_team.group_sale_manager'):
                    raise ValidationError(f'You are not allowed to edit a sales order once it has been confirmed.')
        return super(SaleOrder, self).write(values)
