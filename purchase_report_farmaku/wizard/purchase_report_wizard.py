from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from io import BytesIO
from datetime import datetime
from pytz import timezone
import pytz
import ast
import xlsxwriter
import base64


class PurchaseReportWizard(models.TransientModel):
    _name = "purchase.report.wizard"
    _description = "Purchase Report Wizard"

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
        string='Products')
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    date_start = fields.Date(
        string='Date Start',
        default=datetime.now().strftime('%Y-%m-01'))
    date_end = fields.Date(
        string='Date End',
        default=fields.Date.today)
    type = fields.Selection(
        string='Type',
        selection=[
            ('tracking', 'Tracking'),
            ('change', 'Change'),
        ], required=True)

    def action_generate_report(self):
        report_obj = rec_ids = self.env['purchase.report.farmaku']
        report_obj.delete_existing(trx_type=self.type)
        if self.type == 'tracking':
            query_where = " po.state IN ('purchase','done') "
            if self.partner_ids:
                query_where += f' AND po.partner_id in {str(tuple(self.partner_ids.ids)).replace(",)",")")}'
            if self.date_start:
                query_where += f""" AND po.date_order >= '{self.date_start.strftime("%Y-%m-%d %H:%M:%S")}'"""
            if self.date_end:
                query_where += f""" AND po.date_order <= '{self.date_end.strftime("%Y-%m-%d %H:%M:%S")}'"""
            query = f"""
                SELECT DISTINCT po.id
                FROM purchase_order po  
                WHERE {query_where};
            """
            self.env.cr.execute(query)
            result = self.env.cr.dictfetchall()
            for res in result:
                order_id = res['id']
                order_id = self.env['purchase.order'].search([
                    ('id', '=', order_id),
                ])
                if order_id:
                    confirm_message_id = self.env['mail.message'].search([
                        ('id', 'in', order_id.message_ids.ids),
                        ('subtype_id.name', '=', 'RFQ Confirmed'),
                    ], order='id desc', limit=1)
                    confirm_date = confirm_message_id.date
                    approve_message_id = self.env['mail.message'].search([
                        ('id', 'in', order_id.message_ids.ids),
                        ('subtype_id.name', '=', 'RFQ Approved'),
                    ], order='id desc', limit=1)
                    approve_date = approve_message_id.date
                    rec_ids += report_obj.create({
                        'user_id': self.env.user.id,
                        'order_id': order_id.id,
                        'type': 'tracking',
                        'confirm_date': confirm_date,
                        'approve_date': approve_date,
                    })
        else:
            query_where = " po.state IN ('purchase','done') AND pol.product_id IS NOT NULL "
            if self.partner_ids:
                query_where += f' AND po.partner_id in {str(tuple(self.partner_ids.ids)).replace(",)", ")")}'
            if self.product_ids:
                query_where += f' AND pol.product_id in {str(tuple(self.product_ids.ids)).replace(",)", ")")}'
            if self.date_start:
                query_where += f""" AND po.date_order >= '{self.date_start.strftime("%Y-%m-%d %H:%M:%S")}'"""
            if self.date_end:
                query_where += f""" AND po.date_order <= '{self.date_end.strftime("%Y-%m-%d %H:%M:%S")}'"""
            query = f"""
                SELECT DISTINCT pol.product_id as product_id
                FROM purchase_order_line pol 
                LEFT JOIN purchase_order po ON po.id = pol.order_id
                WHERE {query_where};
            """
            self.env.cr.execute(query)
            result = self.env.cr.dictfetchall()
            for res in result:
                query_where2 = f" AND pol.product_id = {res['product_id']} "
                query = f"""
                    SELECT DISTINCT pol.id, pol.create_date
                    FROM purchase_order_line pol 
                    LEFT JOIN purchase_order po ON po.id = pol.order_id
                    WHERE {query_where + query_where2}
                    ORDER BY pol.create_date asc;
                """
                self.env.cr.execute(query)
                result2 = self.env.cr.dictfetchall()
                old_po_line_id = self.env['purchase.order.line']
                for res2 in result2:
                    po_line_id = res2['id']
                    po_line_id = self.env['purchase.order.line'].search([
                        ('id', '=', po_line_id),
                    ])
                    if old_po_line_id and old_po_line_id.price_unit != po_line_id.price_unit:
                        price_unit = old_po_line_id.product_uom._compute_price(
                            old_po_line_id.price_unit, old_po_line_id.product_id.uom_po_id)
                        new_price_unit = po_line_id.product_uom._compute_price(
                            po_line_id.price_unit, po_line_id.product_id.uom_po_id)
                        if price_unit != new_price_unit:
                            rec_ids += report_obj.create({
                                'user_id': self.env.user.id,
                                'purchase_line_id': old_po_line_id.id,
                                'order_id': old_po_line_id.order_id.id,
                                'type': 'change',
                                'new_purchase_line_id': po_line_id.id,
                            })
                    old_po_line_id = po_line_id
        return rec_ids

    def action_export_excel(self):
        rec_ids = self.action_generate_report()
        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        if self.type == 'tracking':
            report_name = 'Purchase Tracking'
            filename = '%s %s' % (report_name, date_string)

            columns = [
                ('No', 5, 'no', 'no'),
                ('PO Reference', 20, 'char', 'char'),
                ('Vendor', 40, 'char', 'char'),
                ('Warehouse', 20, 'char', 'char'),
                ('Purchase Representative', 20, 'char', 'char'),
                ('Created Date', 20, 'char', 'char'),
                ('RFQ Confirmed Date', 20, 'char', 'char'),
                ('RFQ Approved Date', 20, 'char', 'char'),
                ('PO Receipt Date', 20, 'char', 'char'),
            ]

            worksheet = workbook.add_worksheet(report_name)
            worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])

            row = 5

            col = 0
            for column in columns:
                column_name = column[0]
                column_width = column[1]
                worksheet.set_column(col, col, column_width)
                wbf_color = wbf['header_orange']
                worksheet.write(row, col, column_name, wbf_color)

                col += 1

            row += 1
            no = 1

            for rec_id in rec_ids:
                create_date = fields.Datetime.to_string(pytz.UTC.localize(rec_id.create_date).
                                                        astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))) \
                    if rec_id.create_date else ''
                confirm_date = fields.Datetime.to_string(pytz.UTC.localize(rec_id.confirm_date).
                                                         astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))) \
                    if rec_id.confirm_date else ''
                approve_date = fields.Datetime.to_string(pytz.UTC.localize(rec_id.approve_date).
                                                         astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))) \
                    if rec_id.approve_date else ''
                receipt_date = fields.Datetime.to_string(pytz.UTC.localize(rec_id.receipt_date).
                                                         astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))) \
                    if rec_id.receipt_date else ''
                worksheet.write(row, 0, no, wbf['content_no'])
                worksheet.write(row, 1, rec_id.order_id.name or '', wbf['content'])
                worksheet.write(row, 2, rec_id.partner_id.name or '', wbf['content'])
                worksheet.write(row, 3, rec_id.warehouse_id.name or '', wbf['content'])
                worksheet.write(row, 4, rec_id.representative_user_id.name or '', wbf['content'])
                worksheet.write(row, 5, create_date, wbf['content'])
                worksheet.write(row, 6, confirm_date, wbf['content'])
                worksheet.write(row, 7, approve_date, wbf['content'])
                worksheet.write(row, 8, receipt_date, wbf['content'])

                no += 1
                row += 1

            row += 1
            worksheet.write('A%s' % (row + 2), 'Date %s (%s)' % (datetime_string, self.env.user.tz or 'Asia/Jakarta'),
                            wbf['content_datetime'])
            row -= 1
            worksheet.write(row, 0, '', wbf['total_orange'])
            worksheet.write(row, 1, '', wbf['total_orange'])
            worksheet.write(row, 2, '', wbf['total_orange'])
            worksheet.write(row, 3, '', wbf['total_orange'])
            worksheet.write(row, 4, '', wbf['total_orange'])
            worksheet.write(row, 5, '', wbf['total_orange'])
            worksheet.write(row, 6, '', wbf['total_orange'])
            worksheet.write(row, 7, '', wbf['total_orange'])
            worksheet.write(row, 8, '', wbf['total_orange'])
        else:
            report_name = 'Purchase Price Change'
            filename = '%s %s' % (report_name, date_string)

            columns = [
                ('No', 5, 'no', 'no'),
                ('Product', 60, 'char', 'char'),
                ('PO Reference (Lama)', 20, 'char', 'char'),
                ('Created Date (Lama)', 20, 'char', 'char'),
                ('Receipt Date (Lama)', 20, 'char', 'char'),
                ('Unit Price (Lama)', 20, 'float', 'float'),
                ('Vendor (Lama)', 40, 'char', 'char'),
                ('PO Reference (Baru)', 20, 'char', 'char'),
                ('Created Date (Baru)', 20, 'char', 'char'),
                ('Receipt Date (Baru)', 20, 'char', 'char'),
                ('Unit Price (Baru)', 20, 'float', 'float'),
                ('Vendor (Baru)', 40, 'char', 'char'),
                ('Selisih', 20, 'float', 'float'),
            ]

            worksheet = workbook.add_worksheet(report_name)
            worksheet.merge_range('A2:M3', report_name, wbf['title_doc'])

            row = 5

            col = 0
            for column in columns:
                column_name = column[0]
                column_width = column[1]
                worksheet.set_column(col, col, column_width)
                wbf_color = wbf['header_orange']
                worksheet.write(row, col, column_name, wbf_color)

                col += 1

            row += 1
            no = 1

            price_dif_total = 0
            for rec_id in rec_ids:
                create_date = fields.Datetime.to_string(pytz.UTC.localize(rec_id.create_date).
                                                        astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))) \
                    if rec_id.create_date else ''
                receipt_date = fields.Datetime.to_string(pytz.UTC.localize(rec_id.receipt_date).
                                                         astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))) \
                    if rec_id.receipt_date else ''
                new_create_date = fields.Datetime.to_string(pytz.UTC.localize(rec_id.new_create_date).
                                                            astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))) \
                    if rec_id.new_create_date else ''
                new_receipt_date = fields.Datetime.to_string(pytz.UTC.localize(rec_id.new_receipt_date).
                                                             astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))) \
                    if rec_id.new_receipt_date else ''
                worksheet.write(row, 0, no, wbf['content_no'])
                worksheet.write(row, 1, rec_id.product_id.display_name or '', wbf['content'])
                worksheet.write(row, 2, rec_id.order_id.name or '', wbf['content'])
                worksheet.write(row, 3, create_date, wbf['content'])
                worksheet.write(row, 4, receipt_date, wbf['content'])
                worksheet.write(row, 5, rec_id.price_unit, wbf['content_float'])
                worksheet.write(row, 6, rec_id.partner_id.display_name or '', wbf['content'])
                worksheet.write(row, 7, rec_id.new_order_id.name or '', wbf['content'])
                worksheet.write(row, 8, new_create_date, wbf['content'])
                worksheet.write(row, 9, new_receipt_date, wbf['content'])
                worksheet.write(row, 10, rec_id.new_price_unit, wbf['content_float'])
                worksheet.write(row, 11, rec_id.new_partner_id.display_name or '', wbf['content'])
                worksheet.write(row, 12, rec_id.price_diff, wbf['content_float'])

                no += 1
                row += 1
                price_dif_total += rec_id.price_diff

            row += 1
            worksheet.write('A%s' % (row + 2), 'Date %s (%s)' % (datetime_string, self.env.user.tz or 'Asia/Jakarta'),
                            wbf['content_datetime'])
            row -= 1
            worksheet.write(row, 0, '', wbf['total_orange'])
            worksheet.write(row, 1, '', wbf['total_orange'])
            worksheet.write(row, 2, '', wbf['total_orange'])
            worksheet.write(row, 3, '', wbf['total_orange'])
            worksheet.write(row, 4, '', wbf['total_orange'])
            worksheet.write(row, 5, '', wbf['total_orange'])
            worksheet.write(row, 6, '', wbf['total_orange'])
            worksheet.write(row, 7, '', wbf['total_orange'])
            worksheet.write(row, 8, '', wbf['total_orange'])
            worksheet.write(row, 9, '', wbf['total_orange'])
            worksheet.write(row, 10, '', wbf['total_orange'])
            worksheet.write(row, 11, '', wbf['total_orange'])
            worksheet.write(row, 12, price_dif_total, wbf['total_float_orange'])
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
        if self.type == 'tracking':
            name = 'Purchase Tracking'
            tree_view_id = self.env.ref('purchase_report_farmaku.purchase_report_farmaku_tracking_view_tree')
        else:
            name = 'Purchase Change Price'
            tree_view_id = self.env.ref('purchase_report_farmaku.purchase_report_farmaku_change_view_tree')
        return {
            'name': _(name),
            'view_mode': 'tree',
            'res_model': 'purchase.report.farmaku',
            'domain': [
                ('id', 'in', rec_ids.ids),
            ],
            'view_id': tree_view_id.id,
            'type': 'ir.actions.act_window',
            'context': {},
        }
