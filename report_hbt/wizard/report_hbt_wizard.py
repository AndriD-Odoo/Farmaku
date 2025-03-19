from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import ast
import xlsxwriter
import base64
from io import BytesIO
from datetime import datetime
from pytz import timezone
import pytz


class ReportHbtWizard(models.TransientModel):
    _name = "report.hbt.wizard"
    _description = "Report HBT Wizard"

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))

    name = fields.Char()
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        domain=[('supplier_rank', '!=', 0)],
        string='Vendor')
    product_ids = fields.Many2many(
        comodel_name='product.product',
        string='Product')
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)

    def action_generate_report(self):
        report_obj = rec_ids = self.env['report.hbt']
        report_obj.delete_existing()
        company_ids = self.env['res.company'].sudo().search([])
        company_partner_ids = company_ids.partner_id
        query_where = "po.state IN ('purchase','done') AND pol.product_id IS NOT NULL"
        query_where += f' AND po.partner_id not in {str(tuple(company_partner_ids.ids)).replace(",)",")")}'
        if self.partner_ids:
            query_where += f' AND po.partner_id in {str(tuple(self.partner_ids.ids)).replace(",)",")")}'
        if self.product_ids:
            query_where += f' AND pol.product_id in {str(tuple(self.product_ids.ids)).replace(",)", ")")}'
        query = f"""
            SELECT DISTINCT pol.product_id as product_id
            FROM purchase_order_line pol 
            LEFT JOIN purchase_order po ON po.id = pol.order_id 
            WHERE {query_where};
        """
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()
        for res in result:
            product_id = res['product_id']
            line_id = self.env['purchase.order.line'].search([
                ('product_id', '=', product_id),
                ('order_id.state', 'in', ('purchase', 'done')),
                ('qty_received', '!=', 0),
                ('order_id.partner_id', 'not in', company_partner_ids.ids),
            ], order='create_date desc', limit=1)
            if line_id:
                rec_ids += report_obj.create({
                    'user_id': self.env.user.id,
                    'line_id': line_id.id,
                    'product_id': line_id.product_id.id,
                    'partner_id': line_id.order_id.partner_id.id,
                    'order_id': line_id.order_id.id,
                    'exclude_from_tree': False,
                })
                query_where2 = f' AND po.partner_id != {line_id.order_id.partner_id.id} AND pol.product_id = {product_id} '
                query = f"""
                    SELECT DISTINCT (pol.product_id, po.partner_id) as product_partner
                    FROM purchase_order_line pol 
                    LEFT JOIN purchase_order po ON po.id = pol.order_id 
                    WHERE {query_where + query_where2};
                """
                self.env.cr.execute(query)
                result2 = self.env.cr.fetchall()
                for res2 in result2:
                    product_id, partner_id = ast.literal_eval(res2[0])
                    line_id = self.env['purchase.order.line'].search([
                        ('product_id', '=', product_id),
                        ('order_id.partner_id', '=', partner_id),
                        ('order_id.state', 'in', ('purchase', 'done')),
                        ('qty_received', '!=', 0),
                        ('order_id.partner_id', 'not in', company_partner_ids.ids),
                    ], order='create_date desc', limit=1)
                    if line_id:
                        rec_ids += report_obj.create({
                            'user_id': self.env.user.id,
                            'line_id': line_id.id,
                            'product_id': line_id.product_id.id,
                            'partner_id': line_id.order_id.partner_id.id,
                            'order_id': line_id.order_id.id,
                            'exclude_from_tree': True,
                        })
        return rec_ids

    def action_export_excel(self):
        rec_ids = self.action_generate_report()
        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        report_name = 'Report HBT'
        filename = '%s %s' % (report_name, date_string)

        columns = [
            ('No', 5, 'no', 'no'),
            ('Internal Reference', 20, 'char', 'char'),
            ('Barcode', 20, 'char', 'char'),
            ('Product Name', 40, 'char', 'char'),
            ('Brand', 20, 'char', 'char'),
            ('Product Category', 60, 'char', 'char'),
            ('PO Unit of Measure', 20, 'char', 'char'),
            ('Conversion', 20, 'float', 'float'),
            ('Cost', 20, 'float', 'float'),
            ('Discount', 20, 'float', 'float'),
            ('Sales Price', 20, 'float', 'float'),
            ('Margin', 20, 'float', 'float'),
            ('PO Reference', 20, 'char', 'char'),
            ('TTB Date', 20, 'char', 'char'),
            ('PO Date', 20, 'char', 'char'),
            ('Vendor / Name', 40, 'char', 'char'),
            ('Vendor / PO Unit of Measure', 30, 'char', 'char'),
            ('Vendor / Conversion', 20, 'float', 'float'),
            ('Vendor / Cost', 20, 'float', 'float'),
            ('Vendor / Discount', 20, 'float', 'float'),
            ('Vendor / PO Reference', 20, 'char', 'char'),
            ('Vendor / TTB Date', 20, 'char', 'char'),
            ('Vendor / PO Date', 20, 'char', 'char'),
        ]

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)

        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:N3', report_name, wbf['title_doc'])
        worksheet.merge_range('A5:O5', 'PO Terakhir Per Produk', wbf['header_orange'])
        worksheet.merge_range('P5:W5', 'PO Terakhir Per Vendor', wbf['header_yellow'])

        row = 5

        col = 0
        for column in columns:
            column_name = column[0]
            column_width = column[1]
            worksheet.set_column(col, col, column_width)
            if col <= 14:
                wbf_color = wbf['header_orange']
            else:
                wbf_color = wbf['header_yellow']
            worksheet.write(row, col, column_name, wbf_color)

            col += 1

        row += 1
        no = 1

        total_cost = 0
        total_vendor_cost = 0
        total_sale = 0
        total_margin = 0
        for rec_id in rec_ids:
            effective_date = fields.Datetime.to_string(pytz.UTC.localize(rec_id.order_id.effective_date).
                                                       astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))) \
                if rec_id.order_id.effective_date else ''
            date_approve = fields.Datetime.to_string(pytz.UTC.localize(rec_id.order_id.date_approve).
                                                     astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))) \
                if rec_id.order_id.date_approve else ''
            worksheet.write(row, 0, no if not rec_id.exclude_from_tree else '', wbf['content_no'])
            worksheet.write(row, 1, rec_id.default_code or '' if not rec_id.exclude_from_tree else '', wbf['content'])
            worksheet.write(row, 2, rec_id.barcode or '' if not rec_id.exclude_from_tree else '', wbf['content'])
            worksheet.write(row, 3, rec_id.name or '' if not rec_id.exclude_from_tree else '', wbf['content'])
            worksheet.write(row, 4, rec_id.brand_id.name or '' if not rec_id.exclude_from_tree else '', wbf['content'])
            worksheet.write(row, 5, rec_id.categ_id.display_name or '' if not rec_id.exclude_from_tree else '', wbf['content'])
            worksheet.write(row, 6, rec_id.uom_po_id.name or '' if not rec_id.exclude_from_tree else '', wbf['content'])
            worksheet.write(row, 7, rec_id.factor_inv or '' if not rec_id.exclude_from_tree else '', wbf['content_float'])
            worksheet.write(row, 8, rec_id.cost or '' if not rec_id.exclude_from_tree else '', wbf['content_float'])
            worksheet.write(row, 9, rec_id.discount or '' if not rec_id.exclude_from_tree else '', wbf['content_float'])
            worksheet.write(row, 10, rec_id.lst_price or '' if not rec_id.exclude_from_tree else '', wbf['content_float'])
            worksheet.write(row, 11, rec_id.margin or '' if not rec_id.exclude_from_tree else '', wbf['content_float'])
            worksheet.write(row, 12, rec_id.order_id.name or '' if not rec_id.exclude_from_tree else '', wbf['content'])
            worksheet.write(row, 13, effective_date if not rec_id.exclude_from_tree else '', wbf['content'])
            worksheet.write(row, 14, date_approve if not rec_id.exclude_from_tree else '', wbf['content'])
            worksheet.write(row, 15, rec_id.partner_id.name or '', wbf['content'])
            worksheet.write(row, 16, rec_id.uom_po_id.name or '', wbf['content'])
            worksheet.write(row, 17, rec_id.factor_inv or '', wbf['content_float'])
            worksheet.write(row, 18, rec_id.line_id.product_uom._compute_price(
                rec_id.line_id.price_unit, rec_id.line_id.product_id.uom_id) or '', wbf['content_float'])
            worksheet.write(row, 19, rec_id.discount or '', wbf['content_float'])
            worksheet.write(row, 20, rec_id.order_id.name or '', wbf['content'])
            worksheet.write(row, 21, effective_date or '', wbf['content'])
            worksheet.write(row, 22, date_approve or '', wbf['content'])

            total_vendor_cost += rec_id.cost
            if not rec_id.exclude_from_tree:
                total_cost += rec_id.cost
                total_sale += rec_id.lst_price
                total_margin += rec_id.margin
                no += 1
            row += 1

        row += 1
        worksheet.merge_range('A%s:B%s' % (row, row), 'Grand Total', wbf['total_orange'])
        worksheet.write('A%s' % (row + 2), 'Date %s (%s)' % (datetime_string, self.env.user.tz or 'Asia/Jakarta'),
                        wbf['content_datetime'])
        row -= 1
        worksheet.write(row, 2, '', wbf['total_orange'])
        worksheet.write(row, 3, '', wbf['total_orange'])
        worksheet.write(row, 4, '', wbf['total_orange'])
        worksheet.write(row, 5, '', wbf['total_orange'])
        worksheet.write(row, 6, '', wbf['total_orange'])
        worksheet.write(row, 7, '', wbf['total_orange'])
        worksheet.write(row, 8, total_cost, wbf['total_float_orange'])
        worksheet.write(row, 9, '', wbf['total_orange'])
        worksheet.write(row, 10, total_sale, wbf['total_float_orange'])
        worksheet.write(row, 11, total_margin, wbf['total_float_orange'])
        worksheet.write(row, 12, '', wbf['total_orange'])
        worksheet.write(row, 13, '', wbf['total_orange'])
        worksheet.write(row, 14, '', wbf['total_orange'])
        worksheet.write(row, 15, '', wbf['total_yellow'])
        worksheet.write(row, 16, '', wbf['total_yellow'])
        worksheet.write(row, 17, '', wbf['total_yellow'])
        worksheet.write(row, 18, total_vendor_cost, wbf['total_float_yellow'])
        worksheet.write(row, 19, '', wbf['total_yellow'])
        worksheet.write(row, 20, '', wbf['total_yellow'])
        worksheet.write(row, 21, '', wbf['total_yellow'])
        worksheet.write(row, 22, '', wbf['total_yellow'])
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

    def action_view(self):
        rec_ids = self.action_generate_report()
        return {
            'name': _('Report HBT'),
            'view_mode': 'tree',
            'res_model': 'report.hbt',
            'domain': [
                ('id', 'in', rec_ids.ids),
                ('exclude_from_tree', '=', False),
            ],
            'view_id': self.env.ref('report_hbt.report_hbt_view_tree').id,
            'type': 'ir.actions.act_window',
            'context': {},
        }
