from odoo import fields, models, api
from datetime import datetime, timedelta
from pytz import timezone
from io import BytesIO
from dateutil.relativedelta import relativedelta
import pytz
import xlsxwriter
import base64

MOVE_CATEGORY_MAPPING = {
    False: False,
    'fast': 'F',
    'medium': 'M',
    'slow': 'S',
}


class OrderpointReportWizard(models.TransientModel):
    _name = 'orderpoint.report.wizard'
    _description = 'Reordering Rules Report'

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))

    product_ids = fields.Many2many(
        comodel_name='product.product',
        string='Product',
        required=False)
    brand_ids = fields.Many2many(
        comodel_name='product.brand',
        string='Brand',
        required=False)
    dot_color_ids = fields.Many2many(
        comodel_name='product.dot.color',
        string='Dot Color',
        required=False)
    warehouse_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=False)
    move_category_ids = fields.Many2many(
        comodel_name='product.move.category',
        string='Move Categories')
    min_stock_category = fields.Selection(
        string='Product Display',
        selection=[
            ('w', 'Wajib'),
            ('t', 'Tidak Wajib'),
            ('f', 'Not Set'),
        ], required=False)
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)

    def get_field_string(self):
        products = ''
        brands = ''
        dot_colors = ''
        warehouses = ''
        move_categories = ''
        min_stock_category = ''
        if self.product_ids:
            products = ', '.join(prod.name for prod in self.product_ids)
        if self.brand_ids:
            brands = ', '.join(brand.name for brand in self.brand_ids)
        if self.dot_color_ids:
            dot_colors = ', '.join(dot.name for dot in self.dot_color_ids)
        if self.warehouse_ids:
            warehouses = ', '.join(wh.name for wh in self.warehouse_ids)
        if self.warehouse_ids:
            warehouses = ', '.join(wh.name for wh in self.warehouse_ids)
        if self.move_category_ids:
            move_categories = ', '.join(c.display_name for c in self.move_category_ids)
        if self.min_stock_category == 'w':
            min_stock_category = 'Wajib'
        elif self.min_stock_category == 't':
            min_stock_category = 'Tidak Wajib'
        return products, brands, dot_colors, warehouses, move_categories, min_stock_category

    def get_product_reordering(self):
        query_where = "swo.active = True"
        if self.product_ids:
            query_where += f' AND swo.product_id in {str(tuple(self.product_ids.ids)).replace(",)", ")")}'
        if self.brand_ids:
            query_where += f' AND pt.brand_id in {str(tuple(self.brand_ids.ids)).replace(",)", ")")}'
        if self.dot_color_ids:
            query_where += f' AND pt.product_dot_color_id in {str(tuple(self.dot_color_ids.ids)).replace(",)", ")")}'
        if self.warehouse_ids:
            query_where += f' AND swo.warehouse_id in {str(tuple(self.warehouse_ids.ids)).replace(",)", ")")}'
        if self.move_category_ids:
            query_where += f' AND swo.move_category_id in {str(tuple(self.move_category_ids.ids)).replace(",)", ")")}'
        if self.min_stock_category:
            if self.min_stock_category == 'w':
                query_where += f" AND swo.min_stock_category = 'w'"
            elif self.min_stock_category == 't':
                query_where += f" AND swo.min_stock_category = 't'"
            elif self.min_stock_category == 'f':
                query_where += f" AND swo.min_stock_category IS NULL"
        query = f"""
            SELECT 
                DISTINCT(swo.product_id)
            FROM stock_warehouse_orderpoint swo
            INNER JOIN product_product pp on swo.product_id = pp.id
            INNER JOIN product_template pt on pp.product_tmpl_id = pt.id
            WHERE {query_where};
        """
        self.env.cr.execute(query)
        result = self.env.cr.fetchall()
        return result

    def get_data_for_qweb(self):
        product_ids = self.get_product_reordering()
        data_dict = {}
        additional_domain = []
        if self.move_category_ids:
            additional_domain += [
                ('move_category_id', 'in', self.move_category_ids.ids)
            ]
        if self.min_stock_category:
            if self.min_stock_category == 'w':
                additional_domain += [
                    ('min_stock_category', '=', 'w')
                ]
            elif self.min_stock_category == 't':
                additional_domain += [
                    ('min_stock_category', '=', 't')
                ]
            elif self.min_stock_category == 'f':
                additional_domain += [
                    ('min_stock_category', '=', False)
                ]
        orderpoint_ids = self.env['stock.warehouse.orderpoint'].search([
           ('product_id', 'in', product_ids)
        ] + additional_domain)
        product_ids = orderpoint_ids.mapped('product_id')
        for product_id in product_ids:
            product_tmpl_id = product_id.product_tmpl_id
            grouping = (product_tmpl_id.default_code, product_tmpl_id.name, product_tmpl_id.brand_id, product_tmpl_id.categ_id, product_tmpl_id.product_dot_color_id)
            data_dict.setdefault(grouping, [])
            for location_id in self.get_location_ids():
                # harusnya cuman dapet 1
                orderpoint_id = self.env['stock.warehouse.orderpoint'].search([
                    ('product_id', '=', product_id.id),
                    ('location_id', '=', location_id.id)
                ] + additional_domain, limit=1)
                if orderpoint_id:
                    qty_stock = self.get_qty_stock(orderpoint_id)[0]
                    if not qty_stock:
                        qty_stock = 0
                    rfq_qty = int(self.get_rfq_qty(orderpoint_id))
                    ttb_qty = int(self.get_ttb_qty(orderpoint_id))
                    if orderpoint_id.min_stock_category == 'w':
                        wajib = '✅'
                    elif orderpoint_id.min_stock_category == 't':
                        wajib = '❌'
                    else:
                        wajib = ''
                    # pastikan outstanding PO sudah terupdate
                    orderpoint_id._get_outstanding_po()
                    data_dict[grouping].append({
                        'stock': int(qty_stock) or '-',
                        'wajib': wajib,
                        'min': int(orderpoint_id.product_min_qty) or '-',
                        'l30d': int(orderpoint_id.sale_qty) or '-',
                        'l90d': int(orderpoint_id.sale_qty_90d) or '-',
                        'a90d': int(orderpoint_id.sale_avg_90d) or '-',
                        'category': MOVE_CATEGORY_MAPPING[orderpoint_id.move_category_id.category] or '',
                        'ttb': ttb_qty or '-',
                        'rfq': rfq_qty or '-',
                        'stock_lower_than_min_qty': int(qty_stock) < int(orderpoint_id.product_min_qty),
                        'orderpoint_id': orderpoint_id.id,
                    })
                else:
                    data_dict[grouping].append({
                        'stock': '',
                        'wajib': '',
                        'min': '',
                        'l30d': '',
                        'l90d': '',
                        'a90d': '',
                        'category': '',
                        'ttb': '',
                        'rfq': '',
                        'stock_lower_than_min_qty': False,
                        'orderpoint_id': False,
                    })
        return data_dict

    def action_view_report(self):
        return self.env.ref('stock_extended.action_report_orderpoint').report_action(self.ids)

    def get_data(self):
        product_ids = self.get_product_reordering()
        data_dict = {}
        existing_warehouse_ids = self.env['stock.warehouse']
        additional_domain = []
        if self.move_category_ids:
            additional_domain += [
                ('move_category_id', 'in', self.move_category_ids.ids)
            ]
        if self.min_stock_category:
            if self.min_stock_category == 'w':
                additional_domain += [
                    ('min_stock_category', '=', 'w')
                ]
            elif self.min_stock_category == 't':
                additional_domain += [
                    ('min_stock_category', '=', 't')
                ]
            elif self.min_stock_category == 'f':
                additional_domain += [
                    ('min_stock_category', '=', False)
                ]
        orderpoint_ids = self.env['stock.warehouse.orderpoint'].search([
           ('product_id', 'in', product_ids)
        ] + additional_domain)
        product_ids = orderpoint_ids.mapped('product_id')
        for product_id in product_ids:
            product_tmpl_id = product_id.product_tmpl_id
            grouping = (product_tmpl_id.default_code, product_tmpl_id.name, product_tmpl_id.brand_id, product_tmpl_id.categ_id, product_tmpl_id.product_dot_color_id)
            orderpoint_ids = self.env['stock.warehouse.orderpoint'].search([
                ('product_id', '=', product_id.id)
            ] + additional_domain)
            for op in orderpoint_ids:
                data_dict.setdefault(grouping, {})
                data_dict[grouping].setdefault(op.location_id.display_name, self.env['stock.warehouse.orderpoint'])
                data_dict[grouping][op.location_id.display_name] = data_dict[grouping][op.location_id.display_name] | op
            warehouse_ids = orderpoint_ids.mapped('warehouse_id')
            existing_warehouse_ids |= warehouse_ids
        return data_dict, existing_warehouse_ids

    def get_location_ids(self):
        query_where = "swo.active = True"
        if self.product_ids:
            query_where += f' AND swo.product_id in {str(tuple(self.product_ids.ids)).replace(",)", ")")}'
        if self.brand_ids:
            query_where += f' AND pt.brand_id in {str(tuple(self.brand_ids.ids)).replace(",)", ")")}'
        if self.dot_color_ids:
            query_where += f' AND pt.product_dot_color_id in {str(tuple(self.dot_color_ids.ids)).replace(",)", ")")}'
        if self.warehouse_ids:
            query_where += f' AND swo.warehouse_id in {str(tuple(self.warehouse_ids.ids)).replace(",)", ")")}'
        if self.move_category_ids:
            query_where += f' AND swo.move_category_id in {str(tuple(self.move_category_ids.ids)).replace(",)", ")")}'
        if self.min_stock_category:
            if self.min_stock_category == 'w':
                query_where += f" AND swo.min_stock_category = 'w'"
            elif self.min_stock_category == 't':
                query_where += f" AND swo.min_stock_category = 't'"
            elif self.min_stock_category == 'f':
                query_where += f" AND swo.min_stock_category IS NULL"
        query = f"""
            SELECT 
                DISTINCT(swo.warehouse_id)
            FROM stock_warehouse_orderpoint swo
            INNER JOIN product_product pp on swo.product_id = pp.id
            INNER JOIN product_template pt on pp.product_tmpl_id = pt.id
            WHERE {query_where};
        """
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()
        existing_warehouse_ids = []
        for rec in result:
            existing_warehouse_ids.append(rec['warehouse_id'])
        warehouse_ids = self.warehouse_ids
        if not warehouse_ids:
            warehouse_ids = self.env['stock.warehouse'].search([
                ('company_id', '=', self.env.user.company_id.id),
                ('id', 'in', existing_warehouse_ids),
            ])
        location_ids = warehouse_ids.mapped('lot_stock_id')
        return location_ids

    def get_qty_stock(self, op):
        query = f"""
            SELECT
                sum(available_quantity) as quantity
            FROM
                stock_quant
            WHERE
                product_id = {op.product_id.id} AND
                location_id = {op.location_id.id}
        """
        self.env.cr.execute(query)
        result = self.env.cr.fetchone()
        return result

    def get_rfq_qty(self, op):
        rfq_qty = 0
        warehouse_id = op.warehouse_id
        if warehouse_id:
            query = f"""
                SELECT 
                    DISTINCT(pol.id)
                FROM 
                    purchase_order_line pol
                LEFT JOIN
                    purchase_order po ON po.id = pol.order_id
                LEFT JOIN
                    stock_picking_type spt ON spt.id = po.picking_type_id
                WHERE 
                    po.state in ('draft', 'sent', 'to approve')
                    AND spt.warehouse_id = {warehouse_id.id}
                    AND pol.product_id IS NOT NULL
                    AND pol.product_id = {op.product_id.id}
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
                rfq_qty = sum(l.product_uom._compute_quantity(
                    l.product_qty, l.product_id.uom_id) for l in po_line_ids)
        return rfq_qty

    def get_ttb_qty(self, op):
        outstanding_po_qty = 0
        warehouse_id = op.warehouse_id
        if warehouse_id:
            if op.product_id:
                query = f"""
                    SELECT 
                        DISTINCT(pol.id)
                    FROM 
                        purchase_order_line pol
                    LEFT JOIN
                        purchase_order po ON po.id = pol.order_id
                    LEFT JOIN
                        stock_picking_type spt ON spt.id = po.picking_type_id
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
                        po.state not in ('draft', 'sent', 'to approve', 'cancel')
                        AND spt.warehouse_id = {warehouse_id.id}
                        AND pol.product_id IS NOT NULL
                        AND pol.qty_received < pol.product_uom_qty
                        AND (
                            po.state IN ('purchase', 'done') AND sm.purchase_line_id IS NOT NULL
                            OR
                            po.state NOT IN ('purchase', 'done')
                        )
                        AND pol.product_id = {op.product_id.id}
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
                    outstanding_po_qty = sum(l.product_uom._compute_quantity(
                        l.product_qty - l.qty_received, l.product_id.uom_id) for l in po_line_ids)
            return outstanding_po_qty

    def get_content(self):
        data_dict, existing_warehouse_ids = self.get_data()
        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        product_name = ''
        brand_name = ''
        dot_color_name = ''
        warehouse_name = ''
        move_categories = ''
        min_stock_category = ''
        if self.product_ids:
            product_name = ', '.join(product.name for product in self.product_ids)
        if self.brand_ids:
            brand_name = ', '.join(brand.name for brand in self.brand_ids)
        if self.dot_color_ids:
            dot_color_name = ', '.join(dc.name for dc in self.dot_color_ids)
        if self.warehouse_ids:
            warehouse_name = ', '.join(wh.name for wh in self.warehouse_ids)
        if self.move_category_ids:
            move_categories = ', '.join(c.display_name for c in self.move_category_ids)
        if self.min_stock_category == 'w':
            min_stock_category = 'Wajib'
        elif self.min_stock_category == 't':
            min_stock_category = 'Tidak Wajib'
        elif self.min_stock_category == 'f':
            min_stock_category = 'Not Set'
        report_name = 'Reordering Rules Report'
        filename = '%s %s' % (report_name, date_string)

        op_columns = [
            ('Stock', 6, 'float', 'float'),
            ('W?', 6, 'char', 'char'),
            ('Min', 6, 'float', 'float'),
            ('L30D', 6, 'float', 'float'),
            ('L90D', 6, 'float', 'float'),
            ('A90D', 6, 'float', 'float'),
            ('Cat', 6, 'char', 'char'),
            ('TTB', 6, 'float', 'float'),
            ('RFQ', 6, 'float', 'float')
        ]

        warehouse_ids = self.warehouse_ids
        if not warehouse_ids:
            warehouse_ids = self.env['stock.warehouse'].search([
                ('company_id', '=', self.env.user.company_id.id)
            ])
        warehouse_ids = self.env['stock.warehouse'].search([
            ('id', 'in', warehouse_ids.ids),
            ('id', 'in', existing_warehouse_ids.ids),
        ])
        location_ids = warehouse_ids.mapped('lot_stock_id')

        columns = []
        for location in location_ids:
            columns += [(location.display_name, 15, location.id)]

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
        wbf, workbook = self.add_workbook_format(workbook)

        worksheet = workbook.add_worksheet(report_name)

        worksheet.set_column('A14:A14', 20)
        worksheet.set_column('B15:B15', 30)
        worksheet.set_column('C16:C16', 15)
        worksheet.set_column('D17:D17', 7)

        worksheet.merge_range('A2:C3', report_name, wbf['title_doc'])
        worksheet.write('B5', 'Product', wbf['content_bold'])
        worksheet.merge_range('C5:F5', product_name, wbf['content_bold'])
        worksheet.write('B6', 'Brand', wbf['content_bold'])
        worksheet.merge_range('C6:F6', brand_name, wbf['content_bold'])
        worksheet.write('B7', 'Dot Color', wbf['content_bold'])
        worksheet.merge_range('C7:F7', dot_color_name, wbf['content_bold'])
        worksheet.write('B8', 'Warehouse', wbf['content_bold'])
        worksheet.merge_range('C8:F8', warehouse_name, wbf['content_bold'])
        worksheet.write('B9', 'Move Categories', wbf['content_bold'])
        worksheet.merge_range('C9:F9', move_categories, wbf['content_bold'])
        worksheet.write('B10', 'Product Display', wbf['content_bold'])
        worksheet.merge_range('C10:F10', min_stock_category, wbf['content_bold'])

        col = 4
        row = 12
        worksheet.merge_range('A13:A14', 'Code', wbf['header_orange'])
        worksheet.merge_range('B13:B14', 'Product', wbf['header_orange'])
        worksheet.merge_range('C13:C14', 'Brand', wbf['header_orange'])
        worksheet.merge_range('D13:D14', 'Dot', wbf['header_orange'])

        for column in columns:
            column_name = column[0]
            worksheet.merge_range(
                row, col, row, ((len(op_columns) - 1) + col), column_name, wbf['header_orange_border_right'])
            row += 1
            for op_column in op_columns:
                op_column_name = op_column[0]
                op_column_width = op_column[1]
                worksheet.set_column(col, col, op_column_width)
                if op_column_name == 'RFQ':
                    worksheet.write(row, col, op_column_name, wbf['header_orange_border_right'])
                else:
                    worksheet.write(row, col, op_column_name, wbf['header_orange'])
                col += 1
            row -= 1

        row += 2
        worksheet.freeze_panes(row, 4)
        column_number = {}
        for group, location_name in data_dict.items():
            product_code, product_name, brand_id, categ_id, product_dot_color_id = group
            if product_dot_color_id.name == 'Red':
                wbf_dot_color = wbf['bg_red']
            elif product_dot_color_id.name == 'Blue':
                wbf_dot_color = wbf['bg_blue']
            elif product_dot_color_id.name == 'Green':
                wbf_dot_color = wbf['bg_green']
            elif product_dot_color_id.name == 'Transparent':
                wbf_dot_color = wbf['bg_transparent']
            else:
                wbf_dot_color = wbf['content']
            worksheet.write(row, 0, product_code, wbf['content'])
            worksheet.write(row, 1, product_name, wbf['content'])
            worksheet.write(row, 2, brand_id.name if brand_id else '', wbf['content'])
            worksheet.write(row, 3, '', wbf_dot_color)
            col_loc = 4
            for colum2 in columns:
                loc_vals = location_name.keys()
                if colum2[0] in loc_vals:
                    orderpoint = location_name.get(colum2[0], False)
                    qty_stock = self.get_qty_stock(orderpoint)[0]
                    if not qty_stock:
                        qty_stock = 0
                    rfq_qty = int(self.get_rfq_qty(orderpoint))
                    ttb_qty = int(self.get_ttb_qty(orderpoint))
                    worksheet.write(
                        row, col_loc, int(qty_stock) or '-', wbf['content_number_bold']
                        if qty_stock >= orderpoint.product_min_qty else wbf['content_number_red']
                    )
                    column_number[col_loc] = column_number.get(col_loc, 0) + int(qty_stock)
                    col_loc += 1
                    if orderpoint.min_stock_category == 'w':
                        min_stock_category = '✅'
                    elif orderpoint.min_stock_category == 't':
                        min_stock_category = '❌'
                    else:
                        min_stock_category = ''
                    worksheet.write(row, col_loc, min_stock_category, wbf['content'])
                    col_loc += 1
                    worksheet.write(row, col_loc, int(orderpoint.product_min_qty) or '-', wbf['content_number'])
                    column_number[col_loc] = column_number.get(col_loc, 0) + int(orderpoint.product_min_qty)
                    col_loc += 1
                    worksheet.write(row, col_loc, int(orderpoint.sale_qty) or '-', wbf['content_number'])
                    column_number[col_loc] = column_number.get(col_loc, 0) + int(orderpoint.sale_qty)
                    col_loc += 1
                    worksheet.write(row, col_loc, int(orderpoint.sale_qty_90d) or '-', wbf['content_number'])
                    column_number[col_loc] = column_number.get(col_loc, 0) + int(orderpoint.sale_qty_90d)
                    col_loc += 1
                    worksheet.write(row, col_loc, int(orderpoint.sale_avg_90d) or '-', wbf['content_number'])
                    column_number[col_loc] = column_number.get(col_loc, 0) + int(orderpoint.sale_avg_90d)
                    col_loc += 1
                    worksheet.write(row, col_loc, MOVE_CATEGORY_MAPPING[orderpoint.move_category_id.category] or '', wbf['content'])
                    col_loc += 1
                    # pastikan outstanding PO sudah terupdate
                    orderpoint._get_outstanding_po()
                    worksheet.write(row, col_loc, ttb_qty or '-', wbf['content_number'])
                    column_number[col_loc] = column_number.get(col_loc, 0) + ttb_qty
                    col_loc += 1
                    worksheet.write(row, col_loc, rfq_qty or '-', wbf['content_number_border_right'])
                    column_number[col_loc] = column_number.get(col_loc, 0) + rfq_qty
                    col_loc += 1
                else:
                    worksheet.write(row, col_loc, '', wbf['content'])
                    col_loc += 1
                    worksheet.write(row, col_loc, '', wbf['content'])
                    col_loc += 1
                    worksheet.write(row, col_loc, '', wbf['content'])
                    col_loc += 1
                    worksheet.write(row, col_loc, '', wbf['content'])
                    col_loc += 1
                    worksheet.write(row, col_loc, '', wbf['content'])
                    col_loc += 1
                    worksheet.write(row, col_loc, '', wbf['content'])
                    col_loc += 1
                    worksheet.write(row, col_loc, '', wbf['content'])
                    col_loc += 1
                    worksheet.write(row, col_loc, '', wbf['content'])
                    col_loc += 1
                    worksheet.write(row, col_loc, '', wbf['content_number_border_right'])
                    col_loc += 1
            row += 1

        row += 1
        worksheet.merge_range('A%s:D%s' % (row, row), '', wbf['total_orange'])
        for x in range((len(columns) * 9) + 4):
            if x in (0, 1, 2, 3):
                continue
            wbf_value = wbf['total_number_orange']
            if not (x-3) % 9:
                wbf_value = wbf['total_number_border_right']
            if x in column_number:
                worksheet.write(row - 1, x, '', wbf_value)
            else:
                worksheet.write(row - 1, x, '', wbf_value)

        worksheet.write('A%s' % (row + 2), 'Date %s (%s)' % (datetime_string, self.env.user.tz or 'Asia/Jakarta'),
                        wbf['content_datetime'])
        workbook.close()
        out = base64.encodebytes(fp.getvalue())
        self.write({'datas': out, 'datas_fname': filename})
        return fp, filename

    def print_excel_report(self):
        fp, filename = self.get_content()
        fp.close()
        filename += '%2Exlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=datas&download=true&filename=' + filename,
        }

    def add_workbook_format(self, workbook):
        colors = {
            'white': '#FFFFFF',
            'white_orange': '#FFFFDB',
            'orange': '#FFC300',
            'red': '#FF0000',
            'yellow': '#F6FA03',
            'blue': '#0000FF',
            'green': '#008000',
            'transparent': 'F4F1F0',
        }

        wbf = {}
        wbf['header'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 'font_name': 'Arial'})
        wbf['header'].set_border()

        wbf['header_orange'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['orange'], 'font_color': '#000000', 'valign': 'vcenter',
             'font_name': 'Arial'})
        wbf['header_orange'].set_border()

        wbf['header_orange_border_right'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['orange'], 'font_color': '#000000', 'valign': 'vcenter',
             'font_name': 'Arial'})
        wbf['header_orange_border_right'].set_border()
        wbf['header_orange_border_right'].set_right(2)

        wbf['header_yellow'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['yellow'], 'font_color': '#000000',
             'font_name': 'Arial'})
        wbf['header_yellow'].set_border()

        wbf['header_no'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 'font_name': 'Arial'})
        wbf['header_no'].set_border()
        wbf['header_no'].set_align('vcenter')

        wbf['footer'] = workbook.add_format({'align': 'left', 'font_name': 'Arial'})

        wbf['content_datetime'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss', 'font_name': 'Arial'})
        wbf['content_datetime'].set_left()
        wbf['content_datetime'].set_right()

        wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd', 'font_name': 'Arial'})
        wbf['content_date'].set_left()
        wbf['content_date'].set_right()

        wbf['title_doc'] = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 20,
            'font_name': 'Arial',
        })

        wbf['company'] = workbook.add_format({'align': 'left', 'font_name': 'Arial'})
        wbf['company'].set_font_size(11)

        wbf['content'] = workbook.add_format({'text_wrap': True, 'valign': 'vcenter'})
        wbf['content'].set_left()
        wbf['content'].set_right()

        wbf['content_bold'] = workbook.add_format({'bold': 1})
        wbf['bg_red'] = workbook.add_format({'bg_color': colors['red']})
        wbf['bg_red'].set_top()
        wbf['bg_red'].set_bottom()
        wbf['bg_red'].set_left()
        wbf['bg_red'].set_right()
        wbf['bg_blue'] = workbook.add_format({'bg_color': colors['blue']})
        wbf['bg_blue'].set_top()
        wbf['bg_blue'].set_bottom()
        wbf['bg_blue'].set_left()
        wbf['bg_blue'].set_right()
        wbf['bg_green'] = workbook.add_format({'bg_color': colors['green']})
        wbf['bg_green'].set_top()
        wbf['bg_green'].set_bottom()
        wbf['bg_green'].set_left()
        wbf['bg_green'].set_right()
        wbf['bg_transparent'] = workbook.add_format({'bg_color': colors['transparent']})
        wbf['bg_transparent'].set_top()
        wbf['bg_transparent'].set_bottom()
        wbf['bg_transparent'].set_left()
        wbf['bg_transparent'].set_right()

        wbf['content_center'] = workbook.add_format({'align': 'center'})
        wbf['content_center'].set_left()
        wbf['content_center'].set_right()

        wbf['content_no'] = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        wbf['content_no'].set_left()
        wbf['content_no'].set_right()

        wbf['content_float'] = workbook.add_format({'align': 'right', 'num_format': '#,##0.00', 'font_name': 'Arial', 'valign': 'vcenter'})
        wbf['content_float'].set_right()
        wbf['content_float'].set_left()

        wbf['content_number'] = workbook.add_format({'align': 'right', 'num_format': '#,##0', 'font_name': 'Arial', 'valign': 'vcenter'})
        wbf['content_number'].set_right()
        wbf['content_number'].set_left()

        wbf['content_number_border_right'] = workbook.add_format({
            'align': 'right',
            'num_format': '#,##0',
            'font_name': 'Arial',
            'valign': 'vcenter'
        })
        wbf['content_number_border_right'].set_right(2)
        wbf['content_number_border_right'].set_left()

        wbf['content_number_bold'] = workbook.add_format({
            'align': 'right',
            'num_format': '#,##0',
            'font_name': 'Arial',
            'valign': 'vcenter',
            'bold': 1,
        })
        wbf['content_number_bold'].set_right()
        wbf['content_number_bold'].set_left()

        wbf['content_number_red'] = workbook.add_format({
            'align': 'right',
            'num_format': '#,##0',
            'font_name': 'Arial',
            'valign': 'vcenter',
            'bg_color': 'C3352B',
            'font_color': colors['white'],
            'bold': 1,
        })
        wbf['content_number_red'].set_right()
        wbf['content_number_red'].set_left()

        wbf['content_percent'] = workbook.add_format({'align': 'right', 'num_format': '0.00%', 'font_name': 'Arial'})
        wbf['content_percent'].set_right()
        wbf['content_percent'].set_left()

        wbf['total_float'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['white_orange'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Arial'})
        wbf['total_float'].set_top()
        wbf['total_float'].set_bottom()
        wbf['total_float'].set_left()
        wbf['total_float'].set_right()

        wbf['total_number'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['white_orange'], 'bold': 1, 'num_format': '#,##0',
             'font_name': 'Arial'})
        wbf['total_number'].set_top()
        wbf['total_number'].set_bottom()
        wbf['total_number'].set_left()
        wbf['total_number'].set_right()

        wbf['total'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['white_orange'], 'align': 'center', 'font_name': 'Arial'})
        wbf['total'].set_left()
        wbf['total'].set_right()
        wbf['total'].set_top()
        wbf['total'].set_bottom()

        wbf['total_float_yellow'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['yellow'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Arial'})
        wbf['total_float_yellow'].set_top()
        wbf['total_float_yellow'].set_bottom()
        wbf['total_float_yellow'].set_left()
        wbf['total_float_yellow'].set_right()

        wbf['total_number_yellow'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['yellow'], 'bold': 1, 'num_format': '#,##0', 'font_name': 'Arial'})
        wbf['total_number_yellow'].set_top()
        wbf['total_number_yellow'].set_bottom()
        wbf['total_number_yellow'].set_left()
        wbf['total_number_yellow'].set_right()

        wbf['total_yellow'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['yellow'], 'align': 'center', 'font_name': 'Arial'})
        wbf['total_yellow'].set_left()
        wbf['total_yellow'].set_right()
        wbf['total_yellow'].set_top()
        wbf['total_yellow'].set_bottom()

        wbf['total_float_orange'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['orange'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Arial'})
        wbf['total_float_orange'].set_top()
        wbf['total_float_orange'].set_bottom()
        wbf['total_float_orange'].set_left()
        wbf['total_float_orange'].set_right()

        wbf['total_number_orange'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['orange'], 'bold': 1, 'num_format': '#,##0', 'font_name': 'Arial'})
        wbf['total_number_orange'].set_top()
        wbf['total_number_orange'].set_bottom()
        wbf['total_number_orange'].set_left()
        wbf['total_number_orange'].set_right()

        wbf['total_number_border_right'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['orange'], 'bold': 1, 'num_format': '#,##0', 'font_name': 'Arial'})
        wbf['total_number_border_right'].set_top()
        wbf['total_number_border_right'].set_bottom()
        wbf['total_number_border_right'].set_left()
        wbf['total_number_border_right'].set_right(2)

        wbf['total_orange'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['orange'], 'align': 'center', 'font_name': 'Arial', 'num_format': '#,##0.00'})
        wbf['total_orange'].set_left()
        wbf['total_orange'].set_right()
        wbf['total_orange'].set_top()
        wbf['total_orange'].set_bottom()

        wbf['header_detail_space'] = workbook.add_format({'font_name': 'Arial'})
        wbf['header_detail_space'].set_left()
        wbf['header_detail_space'].set_right()
        wbf['header_detail_space'].set_top()
        wbf['header_detail_space'].set_bottom()

        wbf['header_detail'] = workbook.add_format({'bg_color': '#E0FFC2', 'font_name': 'Arial'})
        wbf['header_detail'].set_left()
        wbf['header_detail'].set_right()
        wbf['header_detail'].set_top()
        wbf['header_detail'].set_bottom()

        return wbf, workbook


class ReportOrderpointWizard(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.stock_extended.orderpoint_report'
    _description = 'Orderpoint Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['orderpoint.report.wizard'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'orderpoint.report.wizard',
            'docs': docs,
            'data': data
        }