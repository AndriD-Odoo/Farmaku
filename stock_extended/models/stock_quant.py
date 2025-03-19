from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import pytz
import logging

_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _compute_value(self):
        super()._compute_value()
        for quant in self:
            # If the user didn't enter a location yet while enconding a quant.
            if not quant.location_id:
                quant.svl_value = 0
                quant.svl_qty = 0
                quant.svl_unit_value = 0
                return

            if not quant.location_id._should_be_valued() or\
                    (quant.owner_id and quant.owner_id != quant.company_id.partner_id):
                quant.svl_value = 0
                quant.svl_qty = 0
                quant.svl_unit_value = 0
                continue
            if quant.product_id.cost_method == 'fifo':
                quantity = quant.product_id.with_company(quant.company_id).quantity_svl
                if float_is_zero(quantity, precision_rounding=quant.product_id.uom_id.rounding):
                    quant.svl_value = 0
                    quant.svl_qty = 0
                    quant.svl_unit_value = 0
                    continue
                average_cost = quant.product_id.with_company(quant.company_id).value_svl / quantity
                quant.svl_value = quant.product_id.with_company(quant.company_id).value_svl
                quant.svl_qty = quantity
                quant.svl_unit_value = average_cost
            else:
                value = quant.quantity * quant.product_id.with_company(quant.company_id).standard_price
                quant.svl_value = value
                quant.svl_qty = quant.quantity
                quant.svl_unit_value = quant.product_id.with_company(quant.company_id).standard_price

    def _compute_avg_value(self):
        for quant in self:
            avg_value = 0
            total_value = 0
            total_qty = 0
            if quant.location_id._should_be_valued():
                all_quant_ids = self.sudo().search([
                    ('product_id', '=', quant.product_id.id),
                    '|',
                    ('location_id.usage', '=', 'internal'),
                    '&',
                    ('location_id.usage', '=', 'transit'),
                    ('location_id.company_id', '!=', False),
                ])
                total_value = sum(all_quant_ids.mapped('value'))
                total_qty = sum(all_quant_ids.mapped('quantity'))
            if total_value and total_qty:
                avg_value = total_value / total_qty
            quant.avg_value = avg_value

    available_quantity = fields.Float(store=True, string='Available', digits='Product Unit of Measure Integer')
    inventory_quantity = fields.Float(string='Qty Fisik', digits='Product Unit of Measure Integer')
    quantity = fields.Float(digits='Product Unit of Measure Integer')
    product_uom_id = fields.Many2one(string='UoM')
    svl_value = fields.Monetary('SVL Value', compute='_compute_value')
    svl_qty = fields.Float('SVL Qty', compute='_compute_value')
    svl_unit_value = fields.Monetary('Unit SVL Value', compute='_compute_value')
    avg_value = fields.Monetary('Avg Value All', compute='_compute_avg_value', compute_sudo=True)

    @api.model
    def create(self, values):
        return super(StockQuant, self).create(values)

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(pytz.timezone(self.env.user.tz or 'Asia/Jakarta'))

    def _send_stock_report(self):
        wizard_id = self.env['stock.report.wizard'].create({})
        wizard_id.send_excel_report()

    def query_update_quant_with_lot(self, quant_id, expiration_date, lot_id):
        query = f"""
            UPDATE
                stock_quant
            SET
                lot_id = {lot_id},
                expiration_date = '{expiration_date}',
                removal_date = '{expiration_date}'
            WHERE
                id = {quant_id.id};
            DO $$
                DECLARE move_id{quant_id.id} INTEGER;
                BEGIN
                INSERT INTO
                    stock_move(
                        name,
                        date,
                        product_id,
                        company_id,
                        product_uom_qty,
                        product_uom,
                        location_id,
                        location_dest_id,
                        picking_type_id,
                        procure_method,
                        state
                    )
                    VALUES(
                        'Create lot for existing stock',
                        '{fields.Datetime.now()}',
                        {quant_id.product_id.id},
                        {quant_id.company_id.id},
                        {quant_id.quantity},
                        {quant_id.product_uom_id.id},
                        {quant_id.location_id.id},
                        {quant_id.location_id.id},
                        {quant_id.location_id.get_warehouse().int_type_id.id},
                        'make_to_stock',
                        'done'
                    )
                RETURNING id INTO move_id{quant_id.id};
                INSERT INTO
                    stock_move_line(
                        move_id,
                        date,
                        product_id,
                        company_id,
                        lot_id,
                        product_uom_qty,
                        qty_done,
                        product_uom_id,
                        location_id,
                        location_dest_id,
                        state
                    )
                    VALUES(
                        move_id{quant_id.id},
                        '{fields.Datetime.now()}',
                        {quant_id.product_id.id},
                        {quant_id.company_id.id},
                        {lot_id},
                        {quant_id.quantity},
                        {quant_id.quantity},
                        {quant_id.product_uom_id.id},
                        {quant_id.location_id.id},
                        {quant_id.location_id.id},
                        'done'
                    );
            END $$;
        """
        return query

    def query_update_quant_without_lot(self, quant_id, expiration_date, lot_name):
        query = f"""
            UPDATE
                stock_quant
            SET
                lot_id = (SELECT id FROM stock_production_lot WHERE name = '{lot_name}' LIMIT 1),
                expiration_date = '{expiration_date}',
                removal_date = '{expiration_date}'
            WHERE
                id = {quant_id.id};
            DO $$
                DECLARE move_id{quant_id.id} INTEGER;
                BEGIN
                INSERT INTO
                    stock_move(
                        name,
                        date,
                        product_id,
                        company_id,
                        product_uom_qty,
                        product_uom,
                        location_id,
                        location_dest_id,
                        picking_type_id,
                        procure_method,
                        state
                    )
                    VALUES(
                        'Create lot for existing stock',
                        '{fields.Datetime.now()}',
                        {quant_id.product_id.id},
                        {quant_id.company_id.id},
                        {quant_id.quantity},
                        {quant_id.product_uom_id.id},
                        {quant_id.location_id.id},
                        {quant_id.location_id.id},
                        {quant_id.location_id.get_warehouse().int_type_id.id},
                        'make_to_stock',
                        'done'
                    )
                RETURNING id INTO move_id{quant_id.id};
                INSERT INTO
                    stock_move_line(
                        move_id,
                        date,
                        product_id,
                        company_id,
                        lot_id,
                        product_uom_qty,
                        qty_done,
                        product_uom_id,
                        location_id,
                        location_dest_id,
                        state
                    )
                    VALUES(
                        move_id{quant_id.id},
                        '{fields.Datetime.now()}',
                        {quant_id.product_id.id},
                        {quant_id.company_id.id},
                        (SELECT id FROM stock_production_lot WHERE name = '{lot_name}' LIMIT 1),
                        {quant_id.quantity},
                        {quant_id.quantity},
                        {quant_id.product_uom_id.id},
                        {quant_id.location_id.id},
                        {quant_id.location_id.id},
                        'done'
                    );
            END $$;
        """
        return query

    def query_get_purchase_date(self, warehouse_id, product_id):
        query = f"""
            SELECT
                CASE
                    WHEN po.effective_date IS NOT NULL THEN po.effective_date
                    WHEN po.date_approve IS NOT NULL THEN po.date_approve
                    WHEN po.date_planned IS NOT NULL THEN po.date_planned
                    ELSE po.date_order
                END AS purchase_date
            FROM
                purchase_order_line pol
            LEFT JOIN
                purchase_order po ON po.id = pol.order_id
            WHERE
                po.state in ('purchase', 'done')
                AND po.picking_type_id = {warehouse_id.in_type_id.id}
                AND pol.product_id = {product_id.id}
            ORDER BY
                po.effective_date DESC,
                po.date_approve DESC
            LIMIT 1
        """
        return query

    def _create_lot_for_existing_stock(self, limit):
        query = """
            SELECT
                q.id
            FROM
                stock_quant q
            LEFT JOIN
                stock_location l ON l.id = q.location_id
            LEFT JOIN
                product_product pp ON pp.id = q.product_id
            LEFT JOIN
                product_template pt ON pt.id = pp.product_tmpl_id
            WHERE
                q.lot_id IS NULL
                AND pt.tracking = 'lot'
                AND l.usage = 'internal'
                AND q.quantity > 0 OR q.quantity IS NULL
                AND pt.active IS TRUE
        """
        if limit:
            query += f' LIMIT {limit}'
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()
        quant_ids = []
        for res in result:
            quant_ids.append(res['id'])
        if not quant_ids:
            raise ValidationError(_('No quant found.'))
        quant_ids = self.env['stock.quant'].sudo().browse(quant_ids)
        insert_query = ''
        lot_names = []
        quant_total = len(quant_ids)
        current_index = 0
        for quant_id in quant_ids:
            current_index += 1
            _logger.info(f'\nProcess current_index/total: ({current_index}/{quant_total})')
            warehouse_id = quant_id.location_id.get_warehouse()
            query = self.query_get_purchase_date(warehouse_id=warehouse_id, product_id=quant_id.product_id)
            self.env.cr.execute(query)
            result = self.env.cr.dictfetchall()
            if not result:
                # cari PO di warehouse yang terakhir kirim stock ke warehouse tsb
                checked_locations = []
                while not result and warehouse_id:
                    warehouse_location_ids = self.env['stock.location'].search([
                        ('id', 'child_of', warehouse_id.view_location_id.ids)
                    ])
                    checked_locations += warehouse_location_ids.ids
                    if not warehouse_location_ids:
                        break
                    warehouse_location_ids = str(tuple(warehouse_location_ids.ids)).replace(',)', ')')
                    query = f"""
                        SELECT
                            sm.id
                        FROM
                            stock_move sm
                        LEFT JOIN
                            stock_location sl ON sl.id = sm.location_id
                        WHERE
                            sm.state = 'done'
                            AND sl.usage = 'internal'
                            AND sm.product_id = {quant_id.product_id.id}
                            AND sm.location_id not in {warehouse_location_ids}
                            AND sm.location_dest_id in {warehouse_location_ids}
                            AND sm.location_id not in {str(tuple(checked_locations)).replace(',)', ')')}
                        ORDER BY
                            sm.date DESC
                        LIMIT 1
                    """
                    self.env.cr.execute(query)
                    result = self.env.cr.dictfetchall()
                    if not result:
                        break
                    last_inter_warehouse_move_id = self.env['stock.move'].browse(result[0]['id'])
                    warehouse_id = last_inter_warehouse_move_id.location_id.get_warehouse()
                    query = self.query_get_purchase_date(warehouse_id=warehouse_id, product_id=quant_id.product_id)
                    self.env.cr.execute(query)
                    result = self.env.cr.dictfetchall()
                if not result:
                    continue
            purchase_date = result[0]['purchase_date']
            expiration_date = purchase_date + relativedelta(days=quant_id.product_id.expiration_time)
            lot_name = ((quant_id.product_id.default_code or '-') + '/' + expiration_date.strftime("%m") +
                        expiration_date.strftime("%y"))
            existing_lot_id = self.env['stock.production.lot'].search([('name', '=', lot_name)], limit=1)
            if existing_lot_id:
                current_query = self.query_update_quant_with_lot(
                    quant_id=quant_id, expiration_date=expiration_date, lot_id=existing_lot_id.id
                )
                insert_query += current_query
            else:
                if lot_name not in lot_names:
                    lot_names.append(lot_name)
                    insert_query += f"""
                        INSERT INTO
                            stock_production_lot(
                                name,
                                product_id,
                                company_id,
                                expiration_date,
                                removal_date,
                                use_date,
                                alert_date
                            )
                            VALUES(
                                '{lot_name}',
                                {quant_id.product_id.id},
                                {quant_id.company_id.id},
                                '{expiration_date}',
                                '{expiration_date}',
                                '{expiration_date}',
                                '{expiration_date}'
                            );
                    """
                current_query = self.query_update_quant_without_lot(
                    quant_id=quant_id, expiration_date=expiration_date, lot_name=lot_name
                )
            insert_query += current_query
        if insert_query:
            self.env.cr.execute(insert_query)

    @api.model
    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None,
                                  strict=False):
        self = self.sudo()
        rounding = product_id.uom_id.rounding
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                              strict=strict)
        if float_compare(quantity, 0, precision_rounding=rounding) < 0:
            available_quantity = sum(quants.mapped('reserved_quantity'))
            if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
                quantity = -available_quantity
        res = super()._update_reserved_quantity(product_id=product_id, location_id=location_id, quantity=quantity,
                                                lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                                                strict=strict)
        return res

    def _cron_reserved_qty_correction(self):
        query = """
            UPDATE
                stock_quant q
            SET
                reserved_quantity = COALESCE(q2.reserved_quantity, 0),
                available_quantity = (COALESCE(q.quantity, 0) - COALESCE(q2.reserved_quantity, 0))
            FROM (
                SELECT
                    sq.id,
                    SUM(sml.reserved_qty) AS reserved_quantity
                FROM
                    stock_quant sq
                LEFT JOIN
                    stock_location sl ON sl.id = sq.location_id
                LEFT JOIN (
                    SELECT
                        line.product_id,
                        line.lot_id,
                        sl.parent_path,
                        line.product_uom_qty AS reserved_qty
                    FROM
                        stock_move_line line
                    LEFT JOIN
                        stock_location sl ON sl.id = line.location_id
                    WHERE
                        line.state in ('partially_available', 'assigned')
                ) sml ON sml.product_id = sq.product_id AND sml.lot_id = sq.lot_id 
                    AND sml.parent_path ILIKE sl.parent_path || '%'
                GROUP BY
                    sq.id
            ) q2
            WHERE
                q.id = q2.id
        """
        self.env.cr.execute(query)

    def action_view_valuation_details(self):
        self.ensure_one()
        action = self.env.ref('stock_account.stock_valuation_layer_action').read()[0]
        valuation_layer_obj = self.env['stock.valuation.layer'].sudo()
        company_id = self.company_id.id
        criteria = [
            ('product_id', '=', self.product_id.id),
            ('company_id', '=', company_id),
        ]
        if self.env.context.get('to_date'):
            to_date = fields.Datetime.to_datetime(self.env.context['to_date'])
            domain.append(('create_date', '<=', to_date))
        valuation_layer_ids = valuation_layer_obj.search(criteria)
        action['domain'] = [('id', 'in', valuation_layer_ids.ids)]
        return action
