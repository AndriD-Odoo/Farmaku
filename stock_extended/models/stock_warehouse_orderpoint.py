import pytz
import logging
import math

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import add, float_compare, frozendict, split_every, format_date

_logger = logging.getLogger(__name__)


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    def _get_default_move_category(self):
        slow_category_id = self.env.ref('asb_base_farmaku.product_move_category_slow')
        return slow_category_id.id

    @api.depends(
        'product_id',
    )
    def _get_outstanding_po(self):
        for rec in self:
            outstanding_po_ids = self.env['purchase.order']
            outstanding_po_qty = 0
            if rec.product_id:
                query = f"""
                    SELECT 
                        DISTINCT(pol.id)
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
                        AND pol.qty_received < pol.product_uom_qty
                        AND (
                            po.state IN ('purchase', 'done') AND sm.purchase_line_id IS NOT NULL
                            OR
                            po.state NOT IN ('purchase', 'done')
                        )
                        AND pol.product_id = {rec.product_id.id}
                    ORDER BY
                        pol.id
                """
                self.env.cr.execute(query)
                result = self.env.cr.dictfetchall()
                po_line_ids = []
                for res in result:
                    po_line_ids.append(res['id'])
                if po_line_ids:
                    po_line_ids = self.env['purchase.order.line'].browse(po_line_ids)
                    outstanding_po_ids = po_line_ids.mapped('order_id')
                    outstanding_po_qty = sum(l.product_uom._compute_quantity(
                        l.product_qty - l.qty_received, l.product_id.uom_id) for l in po_line_ids)
            rec.outstanding_po_ids = outstanding_po_ids
            rec.outstanding_po_qty = outstanding_po_qty

    @api.depends('qty_multiple', 'qty_forecast', 'product_min_qty', 'product_max_qty')
    def _compute_qty_to_order(self):
        # default nya yang dibuatkan PO adalah jika forecast < min_qty
        # diubah jadi forecast <= min_qty
        orderpoint_assigned = self.env['stock.warehouse.orderpoint']
        for orderpoint in self:
            if not orderpoint.product_id or not orderpoint.location_id:
                orderpoint.qty_to_order = False
                continue
            qty_to_order = 0.0
            rounding = orderpoint.product_uom.rounding
            if float_compare(orderpoint.qty_forecast, orderpoint.product_min_qty, precision_rounding=rounding) == 0:
                qty_to_order = max(orderpoint.product_min_qty, orderpoint.product_max_qty) - orderpoint.qty_forecast

                remainder = orderpoint.qty_multiple > 0 and qty_to_order % orderpoint.qty_multiple or 0.0
                if float_compare(remainder, 0.0, precision_rounding=rounding) > 0:
                    qty_to_order += orderpoint.qty_multiple - remainder
                orderpoint.qty_to_order = qty_to_order
                orderpoint_assigned |= orderpoint
        super(StockWarehouseOrderpoint, self-orderpoint_assigned)._compute_qty_to_order()

    sale_qty = fields.Float(
        string='Transaction Qty on Last 30 Days',
        copy=False)
    sale_count = fields.Float(
        string='Transaction Count on Last 30 Days',
        copy=False)
    sale_qty_90d = fields.Float(
        string='Transaction Qty on Last 90 Days',
        copy=False)
    sale_count_90d = fields.Float(
        string='Transaction Count on Last 90 Days',
        copy=False)
    sale_avg_90d = fields.Float(
        string='A90D',
        copy=False)
    move_category_id = fields.Many2one(
        comodel_name='product.move.category',
        string='Move Category',
        default=_get_default_move_category)
    category = fields.Selection(related='move_category_id.category')
    min_buffer = fields.Float(related='move_category_id.min_buffer')
    max_buffer = fields.Float(related='move_category_id.max_buffer')
    outstanding_po_ids = fields.Many2many(
        comodel_name='purchase.order',
        compute='_get_outstanding_po',
        string='Reference Number',
        store=True)
    outstanding_po_qty = fields.Float(
        string='Qty',
        compute='_get_outstanding_po',
        store=True)
    last_sale_date = fields.Datetime(
        string='Last SO Date',
        required=False)
    last_sale_number = fields.Char(
        string='Last SO Number',
        required=False)
    last_update_date = fields.Datetime(
        string='Last Update',
        required=False)
    last_sale_update_date = fields.Datetime(
        string='Last Sale Update',
        required=False)
    min_stock_category = fields.Selection(
        string='Product Display',
        selection=[
            ('w', 'Wajib'),
            ('t', 'Tidak Wajib'),
        ], required=False)
    min_stock = fields.Float(string='Min Stock')
    product_type_id = fields.Many2one('product.type', string='Product Type', related='product_id.product_type_id', store=True)
    product_wajib = fields.Boolean(
        string='Product Wajib',
        compute='get_product_wajib')

    def get_default_min_stock(self, product_id):
        if 'tablet' in product_id.uom_id.name.lower():
            min_stock = self.env['ir.config_parameter'].sudo().get_param('stock_extended.default_min_stock_tablet', 0)
        else:
            min_stock = self.env['ir.config_parameter'].sudo().get_param(
                'stock_extended.default_min_stock_non_tablet', 0)
        return min_stock

    @api.model
    def create(self, values):
        res = super(StockWarehouseOrderpoint, self).create(values)
        return res

    def write(self, values):
        res = super(StockWarehouseOrderpoint, self).write(values)
        return res

    @api.onchange('product_id')
    def onchange_product_min_stock(self):
        if self.product_id:
            self.min_stock = self.get_default_min_stock(self.product_id)

    @api.depends('min_stock_category')
    def get_product_wajib(self):
        for rec in self:
            if rec.min_stock_category == 'w':
                rec.product_wajib = True
            else:
                rec.product_wajib = False

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(fields.Datetime.now()).astimezone(
            pytz.timezone(self.env.user.tz or 'Asia/Jakarta'))

    def get_multiple_qty(self, qty, based_qty):
        if not based_qty:
            return qty
        if qty < based_qty:
            return based_qty
        diff = qty % based_qty
        division_result = int(qty / based_qty)
        qty = division_result * based_qty
        if diff:
            qty += based_qty
        return qty

    def action_compute_sale_qty(self):
        total_rules = len(self)
        current_rule = 1
        for rec in self:
            _logger.info(f'Process sale reordering rules {current_rule}/{total_rules}')
            current_rule += 1
            warehouse_id = rec.location_id.get_warehouse()
            datetime_format = '%Y-%m-%d %H:%M:%S'
            utc = datetime.now().strftime(datetime_format)
            utc = datetime.strptime(utc, datetime_format)
            tz = self.get_default_date_model().strftime(datetime_format)
            tz = datetime.strptime(tz, datetime_format)
            duration = tz - utc
            hours = duration.seconds / 60 / 60
            current_date = self.get_default_date_model()
            yesterday = current_date + timedelta(days=-1)
            yesterday = yesterday.strftime('%Y-%m-%d 23:59:59')
            yesterday = datetime.strptime(yesterday, datetime_format) + relativedelta(hours=-hours)
            date_30_days_ago = yesterday + timedelta(days=-30)
            date_90_days_ago = yesterday + timedelta(days=-90)
            exclude_sales_team_ids = []
            exclude_sales_team = self.env['ir.config_parameter'].sudo().get_param('stock_extended.exclude_sales_team')
            if exclude_sales_team:
                exclude_sales_team = exclude_sales_team.replace(' ', '').split(',')
                exclude_sales_team_ids = [int(team_id) for team_id in exclude_sales_team]
            sale_line_domain = [
                ('order_id.state', 'in', ['sale', 'done']),
                ('product_id', '=', rec.product_id.id),
                ('order_id.date_order', '<=', yesterday),
                ('order_id.date_order', '>=', date_30_days_ago),
                ('order_id.warehouse_id', '=', warehouse_id.id),
                ('order_id.team_id', 'not in', exclude_sales_team_ids),
            ]
            pos_line_domain = [
                ('order_id.state', 'in', ['paid', 'done', 'invoiced']),
                ('product_id', '=', rec.product_id.id),
                ('order_id.date_order', '<=', yesterday),
                ('order_id.date_order', '>=', date_30_days_ago),
                ('order_id.session_id.config_id.picking_type_id.warehouse_id', '=', warehouse_id.id),
                ('order_id.crm_team_id', 'not in', exclude_sales_team_ids),
            ]
            sale_line_ids = self.env['sale.order.line'].sudo().search(sale_line_domain)
            pos_line_ids = self.env['pos.order.line'].sudo().search(pos_line_domain)
            sale_qty = 0
            sale_order_ids = self.env['sale.order']
            pos_order_ids = self.env['pos.order']
            for sale_line_id in sale_line_ids:
                sale_qty += sale_line_id.product_uom._compute_quantity(sale_line_id.product_uom_qty,
                                                                       sale_line_id.product_id.uom_id)
                sale_order_ids |= sale_line_id.order_id
            for pos_line_id in pos_line_ids:
                sale_qty += pos_line_id.product_uom_id._compute_quantity(pos_line_id.qty, pos_line_id.product_id.uom_id)
                pos_order_ids |= pos_line_id.order_id
            sale_count = len(sale_order_ids) + len(pos_order_ids)
            sale_line_domain = [
                ('order_id.state', 'in', ['sale', 'done']),
                ('product_id', '=', rec.product_id.id),
                ('order_id.date_order', '<=', yesterday),
                ('order_id.date_order', '>=', date_90_days_ago),
                ('order_id.warehouse_id', '=', warehouse_id.id),
                ('order_id.team_id', 'not in', exclude_sales_team_ids),
                ('id', 'not in', sale_line_ids.ids),
            ]
            pos_line_domain = [
                ('order_id.state', 'in', ['paid', 'done', 'invoiced']),
                ('product_id', '=', rec.product_id.id),
                ('order_id.date_order', '<=', yesterday),
                ('order_id.date_order', '>=', date_90_days_ago),
                ('order_id.session_id.config_id.picking_type_id.warehouse_id', '=', warehouse_id.id),
                ('order_id.crm_team_id', 'not in', exclude_sales_team_ids),
                ('id', 'not in', pos_line_ids.ids),
            ]
            sale_line_ids = self.env['sale.order.line'].sudo().search(sale_line_domain)
            pos_line_ids = self.env['pos.order.line'].sudo().search(pos_line_domain)
            sale_qty_90d = sale_qty
            sale_order_90d_ids = self.env['sale.order']
            pos_order_90d_ids = self.env['pos.order']
            for sale_line_id in sale_line_ids:
                sale_qty_90d += sale_line_id.product_uom._compute_quantity(sale_line_id.product_uom_qty,
                                                                           sale_line_id.product_id.uom_id)
                sale_order_90d_ids |= sale_line_id.order_id
            for pos_line_id in pos_line_ids:
                sale_qty_90d += pos_line_id.product_uom_id._compute_quantity(pos_line_id.qty,
                                                                             pos_line_id.product_id.uom_id)
                pos_order_90d_ids |= pos_line_id.order_id
            sale_count_90d = sale_count + len(sale_order_90d_ids) + len(pos_order_90d_ids)
            sale_avg_90d = sale_qty_90d / 3.0
            rec.sudo().write({
                'sale_qty': sale_qty,
                'sale_count': sale_count,
                'sale_qty_90d': sale_qty_90d,
                'sale_count_90d': sale_count_90d,
                'sale_avg_90d': sale_avg_90d,
                'last_sale_update_date': fields.Datetime.now(),
            })

    def action_compute_min_max(self, manual=True):
        total_rules = len(self)
        current_rule = 1
        slow_category_id = self.env.ref('asb_base_farmaku.product_move_category_slow')
        medium_category_id = self.env.ref('asb_base_farmaku.product_move_category_medium')
        fast_category_id = self.env.ref('asb_base_farmaku.product_move_category_fast')
        for rec in self:
            _logger.info(f'Process min max reordering rules {current_rule}/{total_rules}')
            current_rule += 1
            if manual:
                rec.action_compute_sale_qty()
            if rec.sale_count > fast_category_id.sale_last_30_days:
                move_category_id = fast_category_id
            elif slow_category_id.sale_last_30_days <= rec.sale_count <= fast_category_id.sale_last_30_days:
                move_category_id = medium_category_id
            else:
                move_category_id = slow_category_id
            final_sale_qty = max(rec.sale_qty, rec.sale_avg_90d)
            final_sale_qty = max(final_sale_qty, rec.min_stock)
            po_qty = round(rec.product_id.uom_po_id._compute_quantity(1, rec.product_id.uom_id))
            product_min_qty = math.ceil(final_sale_qty / 30 * move_category_id.min_buffer)
            product_max_qty = math.ceil(final_sale_qty / 30 * move_category_id.max_buffer)
            multiple_sales_conversion_min_qty = self.get_multiple_qty(
                product_min_qty, rec.product_id.sales_conversion_qty)
            multiple_sales_conversion_max_qty = self.get_multiple_qty(
                product_max_qty, rec.product_id.sales_conversion_qty)
            pien_tze_huang = False
            slow_min_qty = self.env['ir.config_parameter'].sudo().get_param('stock_extended.slow_min_qty', 0)
            slow_min_qty = int(slow_min_qty)
            pien_tze_huang_min_qty = self.env['ir.config_parameter'].sudo().get_param(
                'stock_extended.pien_tze_huang_min_qty', 0)
            pien_tze_huang_min_qty = int(pien_tze_huang_min_qty)
            if 'pien tze huang' in rec.product_id.name.lower():
                pien_tze_huang = True
            if rec.product_type_id.ethical:
                if rec.min_stock_category == 't' and move_category_id == slow_category_id and not product_min_qty:
                    product_min_qty = 0
                else:
                    product_min_qty = multiple_sales_conversion_min_qty
            else:
                if pien_tze_huang and product_min_qty <= pien_tze_huang_min_qty:
                    product_min_qty = 3
                elif rec.min_stock_category == 'w':
                    if move_category_id == slow_category_id and product_min_qty <= slow_min_qty:
                        product_min_qty = 3
            product_max_qty = max(product_min_qty, multiple_sales_conversion_max_qty)
            product_max_qty = self.get_multiple_qty(
                product_max_qty, po_qty)
            if rec.min_stock_category == 'w':
                product_min_qty = max(product_min_qty, rec.min_stock)
            rec._get_outstanding_po()
            rec.sudo().write({
                'move_category_id': move_category_id.id,
                'product_min_qty': product_min_qty,
                'product_max_qty': product_max_qty,
                'qty_multiple': po_qty,
                'last_update_date': fields.Datetime.now(),
            })

    def _calculate_reordering_rules(self, type, limit=0):
        """
            PARAMS:
                type = min_max/sale
        """
        # hanya jalankan antara jam 22.00 - 07.00
        current_date = self.get_default_date_model()
        if 7 < current_date.hour < 22:
            return False
        domain = []
        if type == 'min_max':
            date_90_days_ago = fields.Datetime.now() + timedelta(days=-90)
            domain.append(('last_sale_date', '>=', date_90_days_ago))
            domain_last_update = [('last_update_date', '=', False)]
            order = 'last_update_date asc'
        else:
            domain_last_update = [('last_sale_update_date', '=', False)]
            order = 'last_sale_update_date asc'
        rule_ids = self.sudo().search(domain + domain_last_update, order=order, limit=limit)
        if not rule_ids:
            rule_ids = self.sudo().search(domain, order=order, limit=limit)
        if type == 'min_max':
            rule_ids.action_compute_min_max(manual=False)
        else:
            rule_ids.action_compute_sale_qty()

    def update_last_sale_date(self):
        for rec in self:
            rec.update_last_sale_date_by_product_warehouse(
                rec.product_id, rec.location_id.get_warehouse()
            )

    def update_last_sale_date_by_product_warehouse(self, product_ids, warehouse_ids):
        route_id = self.env.ref('purchase_stock.route_warehouse0_buy')
        for warehouse_id in warehouse_ids:
            for product_id in product_ids.filtered(lambda p: p.purchase_ok and p.type == 'product'):
                rule_id = self.sudo().search([
                    ('warehouse_id', '=', warehouse_id.id),
                    ('location_id', '=', warehouse_id.lot_stock_id.id),
                    ('product_id', '=', product_id.id),
                    ('company_id', '=', warehouse_id.company_id.id),
                ], limit=1)
                if not rule_id:
                    rule_id = self.env['stock.warehouse.orderpoint'].create({
                        'warehouse_id': warehouse_id.id,
                        'location_id': warehouse_id.lot_stock_id.id,
                        'product_id': product_id.id,
                        'route_id': route_id.id,
                        'company_id': warehouse_id.company_id.id,
                    })
                if not rule_id.route_id:
                    rule_id.sudo().write({
                        'route_id': route_id.id,
                    })
                exclude_sales_team_ids = []
                exclude_sales_team = self.env['ir.config_parameter'].sudo().get_param(
                    'stock_extended.exclude_sales_team')
                if exclude_sales_team:
                    exclude_sales_team = exclude_sales_team.replace(' ', '').split(',')
                    exclude_sales_team_ids = [int(team_id) for team_id in exclude_sales_team]
                last_sale_line_id = self.env['sale.order.line'].search([
                    ('order_id.state', 'in', ['sale', 'done']),
                    ('product_id', '=', product_id.id),
                    ('order_id.warehouse_id', '=', warehouse_id.id),
                    ('order_id.team_id', 'not in', exclude_sales_team_ids),
                ], limit=1, order='create_date desc')
                rule_id.sudo().write({
                    'last_sale_date': last_sale_line_id.order_id.date_order,
                    'last_sale_number': last_sale_line_id.order_id.name,
                })

    def action_view_purchase(self):
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        action['domain'] = [('id', 'in', self.outstanding_po_ids.ids)]
        return action
