import ast
import xlsxwriter
import base64
import pytz

from io import BytesIO
from datetime import datetime, timedelta
from pytz import timezone
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class NonMovingProductWizard(models.TransientModel):
    _name = "non.moving.product.wizard"
    _description = "Non Moving Product Wizard"

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))

    name = fields.Char()
    day = fields.Integer(string='Day(s)', default=90)
    product_ids = fields.Many2many(
        comodel_name='product.product',
        string='Product')
    storable_product = fields.Boolean(
        string='All Storable Product',
        required=False)
    warehouse_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        string='Warehouse')
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)

    def action_export_excel(self):
        if self.day <= 0:
            raise ValidationError(_('Wrong value for day(s). Please input positive value.'))
        date_filter = datetime.now() - timedelta(days=self.day)
        date_filter = date_filter.strftime('%Y-%m-%d %H:%M:%S')
        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
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
        all_warehouse_ids = self.env['stock.warehouse'].search([])
        report_name = 'Report Non Moving Product'
        filename = '%s %s' % (report_name, date_string)

        columns = [
            ('No', 5, 'no', 'no'),
            ('Internal Reference', 20, 'char', 'char'),
            ('Product Name', 40, 'char', 'char'),
            ('Brand', 20, 'char', 'char'),
            ('Product Category', 60, 'char', 'char'),
            ('Available Quantity', 20, 'float', 'float'),
            ('Stock Value', 20, 'float', 'float'),
            ('Last Date', 20, 'char', 'char'),
            ('Receipt Date', 20, 'char', 'char'),
            ('Sales Price', 20, 'float', 'float'),
            ('Cost Nett', 20, 'float', 'float'),
            ('Margin', 20, 'float', 'float'),
            ('%', 20, 'char', 'char'),
            ('Warehouse', 25, 'char', 'char'),
            ('Total S30D', 20, 'float', 'float'),
            ('Top Seller', 40, 'char', 'char'),
        ]

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)

        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:G3', report_name, wbf['title_doc'])

        row = 4

        col = 0
        for column in columns:
            column_name = column[0]
            column_width = column[1]
            worksheet.set_column(col, col, column_width)
            wbf_color = wbf['header_orange']
            worksheet.write(row, col, column_name, wbf_color)

            col += 1

        warehouse_ids = self.warehouse_ids
        if not warehouse_ids:
            warehouse_ids = all_warehouse_ids
        row += 1
        no = 1

        total_qty = 0
        total_value = 0
        total_sale_price = 0
        total_cost = 0
        total_margin = 0
        grand_total_sale = 0
        for warehouse_id in warehouse_ids:
            location_ids = self.env['stock.location'].search([
                ('id', 'child_of', warehouse_id.view_location_id.ids)
            ])
            location_ids_str = str(tuple(location_ids.ids)).replace(',)', ')')
            query_get_product_received = f"""
                SELECT
                    DISTINCT(sq.product_id) AS product_id
                FROM
                    stock_quant sq
                LEFT JOIN
                    stock_location sl ON sl.id = sq.location_id
                WHERE
                    sq.in_date <= '{date_filter}'
                    AND sl.usage = 'internal'
                    AND sl.id in {location_ids_str}
            """
            query_get_product_moved = f"""
                SELECT
                    DISTINCT(sml.product_id) AS product_id
                FROM
                    stock_move_line sml
                LEFT JOIN
                    stock_location sl ON sl.id = sml.location_id
                LEFT JOIN
                    stock_location dl ON dl.id = sml.location_dest_id
                WHERE
                    sml.date >= '{date_filter}'
                    AND sl.usage = 'internal'
                    AND sl.id in {location_ids_str}
                    AND dl.usage = 'customer'
            """
            query_where = f"""
                pp.id in ({query_get_product_received})
                AND pp.id not in ({query_get_product_moved})
            """
            if self.storable_product:
                query_where += f" AND pt.type = 'product' "
            elif self.product_ids:
                query_where += f' AND pp.id IN {str(tuple(self.product_ids.ids)).replace(",)", ")")} '
            query = f"""
                SELECT
                    DISTINCT(pp.id) AS product_id
                FROM
                    product_product pp
                LEFT JOIN
                    product_template pt ON pt.id = pp.product_tmpl_id
                WHERE
                    {query_where}
            """
            self.env.cr.execute(query)

            result = self.env.cr.dictfetchall()
            for res in result:
                product_id = self.env['product.product'].browse(res['product_id'])
                last_sale_move_line_id = self.env['stock.move.line'].search([
                    ('state', '=', 'done'),
                    ('product_id', '=', product_id.id),
                    ('location_id.usage', '=', 'internal'),
                    ('location_id.id', 'in', location_ids.ids),
                    ('location_dest_id.usage', '=', 'customer'),
                ], order='date desc', limit=1)
                if last_sale_move_line_id:
                    last_date = fields.Datetime.to_string(pytz.UTC.localize(last_sale_move_line_id.date).
                                                          astimezone(timezone(self.env.user.tz or 'Asia/Jakarta')))
                else:
                    last_date = ''
                last_purchase_move_line_id = self.env['stock.move.line'].search([
                    ('state', '=', 'done'),
                    ('product_id', '=', product_id.id),
                    ('location_id.usage', '=', 'supplier'),
                    ('location_dest_id.usage', '=', 'internal'),
                    ('location_dest_id.id', 'in', location_ids.ids),
                ], order='date desc', limit=1)
                if last_purchase_move_line_id:
                    receipt_date = fields.Datetime.\
                        to_string(pytz.UTC.localize(last_purchase_move_line_id.date).
                                  astimezone(timezone(self.env.user.tz or 'Asia/Jakarta')))
                else:
                    receipt_date = ''
                margin = product_id.list_price - product_id.standard_price
                if product_id.list_price:
                    margin_percentage = margin / product_id.list_price * 100
                else:
                    margin_percentage = 0
                exclude_sales_team_ids = []
                exclude_sales_team = self.env['ir.config_parameter'].sudo().get_param(
                    'stock_extended.exclude_sales_team')
                if exclude_sales_team:
                    exclude_sales_team = exclude_sales_team.replace(' ', '').split(',')
                    exclude_sales_team_ids = [int(team_id) for team_id in exclude_sales_team]
                sale_line_domain = [
                    ('order_id.state', 'in', ['sale', 'done']),
                    ('product_id', '=', product_id.id),
                    ('order_id.date_order', '>=', date_30_days_ago),
                    ('order_id.warehouse_id', '=', all_warehouse_ids.ids),
                    ('order_id.team_id', 'not in', exclude_sales_team_ids),
                    ('qty_delivered', '>', 0),
                ]
                sale_line_ids = self.env['sale.order.line'].sudo().search(sale_line_domain)
                seller_warehouse_ids = sale_line_ids.mapped('order_id.warehouse_id')
                sale_total = 0
                warehouse_sale = {}
                top_seller = ''
                for seller_warehouse_id in seller_warehouse_ids:
                    warehouse_sale_line_ids = self.env['sale.order.line'].sudo().search([
                        ('order_id.warehouse_id', '=', seller_warehouse_id.id),
                        ('id', 'in', sale_line_ids.ids),
                    ])
                    for w_line_id in warehouse_sale_line_ids:
                        qty_delivered = w_line_id.product_uom._compute_quantity(w_line_id.qty_delivered, product_id.uom_id)
                        sale_total += qty_delivered
                        warehouse_sale[seller_warehouse_id] = warehouse_sale.get(seller_warehouse_id, 0) + qty_delivered
                # current_warehouse_sale_line_ids = self.env['sale.order.line'].sudo().search([
                #     ('order_id.warehouse_id', '=', warehouse_id.id),
                #     ('id', 'in', sale_line_ids.ids),
                # ])
                # for w_line_id in current_warehouse_sale_line_ids:
                #     qty_delivered = w_line_id.product_uom._compute_quantity(w_line_id.qty_delivered, product_id.uom_id)
                #     sale_total += qty_delivered
                if warehouse_sale:
                    top_seller_warehouse_id = max(warehouse_sale, key= lambda x: warehouse_sale[x])
                    top_seller = top_seller_warehouse_id.display_name
                quant_ids = self.env['stock.quant'].sudo().search([
                    ('location_id', 'child_of', warehouse_id.view_location_id.ids),
                    ('location_id.usage', '=', 'internal'),
                    ('product_id', '=', product_id.id),
                ])
                qty_available = sum(quant_ids.mapped('available_quantity'))
                worksheet.write(row, 0, no, wbf['content_no'])
                worksheet.write(row, 1, product_id.default_code if product_id.default_code else '', wbf['content'])
                worksheet.write(row, 2, product_id.name, wbf['content'])
                worksheet.write(row, 3, product_id.brand_id.name if product_id.brand_id.name else '', wbf['content'])
                worksheet.write(row, 4, product_id.categ_id.display_name, wbf['content'])
                worksheet.write(row, 5, qty_available, wbf['content_float'])
                worksheet.write(row, 6, product_id.standard_price * qty_available, wbf['content_float'])
                worksheet.write(row, 7, last_date, wbf['content'])
                worksheet.write(row, 8, receipt_date, wbf['content'])
                worksheet.write(row, 9, product_id.list_price, wbf['content_float'])
                worksheet.write(row, 10, product_id.standard_price, wbf['content_float'])
                worksheet.write(row, 11, margin, wbf['content_float'])
                worksheet.write(row, 12, f'{round(margin_percentage)} %', wbf['content_center'])
                worksheet.write(row, 13, warehouse_id.name, wbf['content_float'])
                worksheet.write(row, 14, sale_total, wbf['content_float'])
                worksheet.write(row, 15, top_seller, wbf['content'])

                no += 1
                row += 1

                total_qty += qty_available
                total_value += (product_id.standard_price * qty_available)
                total_sale_price += product_id.list_price
                total_cost += product_id.standard_price
                total_margin += margin
                grand_total_sale += sale_total

        row += 1
        worksheet.merge_range('A%s:B%s' % (row, row), 'Grand Total', wbf['total_orange'])
        worksheet.write('A%s' % (row + 2), 'Date %s (%s)' % (datetime_string, self.env.user.tz or 'Asia/Jakarta'),
                        wbf['content_datetime'])
        row -= 1
        worksheet.write(row, 2, '', wbf['total_orange'])
        worksheet.write(row, 3, '', wbf['total_orange'])
        worksheet.write(row, 4, '', wbf['total_orange'])
        worksheet.write(row, 5, total_qty, wbf['total_float_orange'])
        worksheet.write(row, 6, total_value, wbf['total_float_orange'])
        worksheet.write(row, 7, '', wbf['total_orange'])
        worksheet.write(row, 8, '', wbf['total_orange'])
        worksheet.write(row, 9, total_sale_price, wbf['total_float_orange'])
        worksheet.write(row, 10, total_cost, wbf['total_float_orange'])
        worksheet.write(row, 11, total_margin, wbf['total_orange'])
        worksheet.write(row, 12, '', wbf['total_orange'])
        worksheet.write(row, 13, '', wbf['total_orange'])
        worksheet.write(row, 14, grand_total_sale, wbf['total_float_orange'])
        worksheet.write(row, 15, '', wbf['total_orange'])
        workbook.close()
        out = base64.encodebytes(fp.getvalue())
        self.write({'datas': out, 'datas_fname': filename})
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
            'white_orange': '#FFFFDB',
            'orange': '#FFC300',
            'red': '#FF0000',
            'yellow': '#F6FA03',
        }

        wbf = {}
        wbf['header'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 'font_name': 'Arial'})
        wbf['header'].set_border()

        wbf['header_orange'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['orange'], 'font_color': '#000000',
             'font_name': 'Arial'})
        wbf['header_orange'].set_border()

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

        wbf['content'] = workbook.add_format()
        wbf['content'].set_left()
        wbf['content'].set_right()

        wbf['content_center'] = workbook.add_format({'align': 'center'})
        wbf['content_center'].set_left()
        wbf['content_center'].set_right()

        wbf['content_no'] = workbook.add_format({'align': 'center'})
        wbf['content_no'].set_left()
        wbf['content_no'].set_right()

        wbf['content_float'] = workbook.add_format({'align': 'right', 'num_format': '#,##0.00', 'font_name': 'Arial'})
        wbf['content_float'].set_right()
        wbf['content_float'].set_left()

        wbf['content_number'] = workbook.add_format({'align': 'right', 'num_format': '#,##0', 'font_name': 'Arial'})
        wbf['content_number'].set_right()
        wbf['content_number'].set_left()

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

    @api.onchange('storable_product')
    def onchange_storable_product(self):
        if self.storable_product:
            self.product_ids = False

    @api.model
    def default_get(self, fields):
        res = super(NonMovingProductWizard, self).default_get(fields)
        warehouse_ids = self.env['stock.warehouse'].search([
            ('id', 'in', [3, 26, 27, 28, 19, 22, 8, 25, 23, 9, 24, 10, 11, 20, 18, 1])
        ])
        if warehouse_ids:
            res['warehouse_ids'] = [(6, 0, warehouse_ids.ids)]
        return res
