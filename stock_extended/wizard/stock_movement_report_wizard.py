from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from io import BytesIO
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pytz import timezone
from requests.utils import requote_uri
import pytz
import xlsxwriter
import base64


class StockMovementReportWizard(models.TransientModel):
    _name = "stock.movement.report.wizard"
    _description = "Daily Stock Movement Report Wizard .xlsx"
    
    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))
    
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    name = fields.Char(
        string='Name',
        default=_("If the warehouse doesn't appear here, "
                  "it means it hasn't been set as the default warehouse in the user."))
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True)

    def print_excel_report(self):
        datetime_format = '%Y-%m-%d %H:%M:%S'
        utc = datetime.now().strftime(datetime_format)
        utc = datetime.strptime(utc, datetime_format)
        tz = self.get_default_date_model().strftime(datetime_format)
        tz = datetime.strptime(tz, datetime_format)
        duration = tz - utc
        hours = duration.seconds / 60 / 60
        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        report_name = 'Daily Stock Movement Report'
        filename = '%s %s' % (report_name, date_string)

        columns = [
            ('No', 7, 'no', 'no'),
            ('Product Code', 20, 'char', 'char'),
            ('Product Name', 60, 'char', 'char'),
            ('UoM', 20, 'char', 'char'),
            ('Onhand', 20, 'float', 'float'),
            ('Available', 20, 'float', 'float'),
            ('PO', 20, 'float', 'float'),
            ('ITS', 20, 'float', 'float'),
            ('Adjustment', 20, 'float', 'float'),
            ('SO Return', 20, 'float', 'float'),
            ('Sold', 20, 'float', 'float'),
            ('ITS', 20, 'float', 'float'),
            ('Adjustment', 20, 'float', 'float'),
            ('PO Return', 20, 'float', 'float'),
            ('SO', 20, 'float', 'float'),
        ]
        result = []

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)

        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])

        row = 6

        col = 0
        for column in columns:
            column_name = column[0]
            column_width = column[1]
            column_type = column[2]
            worksheet.set_column(col, col, column_width)
            worksheet.write(row - 1, col, column_name, wbf['header_orange'])

            col += 1

        worksheet.merge_range('A5:A6', 'No', wbf['header_orange'])
        worksheet.merge_range('B5:B6', 'Product Code', wbf['header_orange'])
        worksheet.merge_range('C5:C6', 'Product Name', wbf['header_orange'])
        worksheet.merge_range('D5:D6', 'UoM', wbf['header_orange'])
        worksheet.merge_range('E5:F5', 'Stock', wbf['header_orange'])
        worksheet.merge_range('G5:J5', 'In', wbf['header_orange'])
        worksheet.merge_range('K5:O5', 'Out', wbf['header_orange'])
        worksheet.freeze_panes(6, 4)

        row += 1
        no = 1

        current_date = datetime.now()
        current_date = current_date.strftime('%Y-%m-%d 23:59:59')
        end_date = datetime.strptime(current_date, datetime_format) - timedelta(hours=hours)
        start_date = end_date - timedelta(hours=24)
        move_line_ids = self.env['stock.move.line'].sudo().search([
            ('state', '=', 'done'),
            '|',
            ('location_id', 'child_of', self.warehouse_id.view_location_id.ids),
            ('location_dest_id', 'child_of', self.warehouse_id.view_location_id.ids),
            ('date', '<=', end_date),
            ('date', '>', start_date),
        ])
        product_ids = self.env['product.product'].search([
            ('id', 'in', move_line_ids.mapped('product_id').ids)
        ], order='name asc')
        for product_id in product_ids:
            quant_ids = self.env['stock.quant'].sudo().search([
                ('product_id', '=', product_id.id),
                ('location_id', 'child_of', self.warehouse_id.view_location_id.ids),
            ])
            move_line_ids = self.env['stock.move.line'].sudo().search([
                ('product_id', '=', product_id.id),
                ('state', '=', 'done'),
                '|',
                ('location_id', 'child_of', self.warehouse_id.view_location_id.ids),
                ('location_dest_id', 'child_of', self.warehouse_id.view_location_id.id),
                ('date', '<=', end_date),
                ('date', '>', start_date),
            ])
            if not move_line_ids:
                continue
            outstanding_sale_move_ids = self.env['stock.move'].sudo().search([
                ('product_id', '=', product_id.id),
                ('state', 'not in', ['done', 'cancel']),
                ('location_id', 'child_of', self.warehouse_id.view_location_id.id),
                ('location_dest_id.usage', '=', 'customer'),
                ('date', '<=', end_date),
                ('date', '>', start_date),
            ])
            onhand_qty = 0
            available_qty = 0
            purchase_qty = 0
            transfer_in_qty = 0
            adjustment_in_qty = 0
            return_in_qty = 0
            sale_received_qty = 0
            transfer_out_qty = 0
            adjustment_out_qty = 0
            return_out_qty = 0
            sale_outstanding_qty = 0
            for quant_id in quant_ids:
                onhand_qty += quant_id.quantity
                available_qty += (quant_id.quantity - quant_id.reserved_quantity)
            for line_id in move_line_ids:
                qty = line_id.product_uom_id._compute_quantity(line_id.qty_done, line_id.product_id.uom_id)
                if line_id.location_id.usage == 'supplier' and line_id.location_dest_id.usage == 'internal':
                    purchase_qty += qty
                elif line_id.location_id.usage == 'internal' and line_id.location_dest_id.usage == 'internal':
                    if (line_id.location_id.get_warehouse().id != self.warehouse_id.id
                            and line_id.location_dest_id.get_warehouse().id == self.warehouse_id.id):
                        transfer_in_qty += qty
                    elif (line_id.location_id.get_warehouse().id == self.warehouse_id.id
                          and line_id.location_dest_id.get_warehouse().id != self.warehouse_id.id):
                        transfer_out_qty += qty
                elif line_id.location_id.usage == 'inventory' and line_id.location_dest_id.usage == 'internal':
                    adjustment_in_qty += qty
                elif line_id.location_id.usage == 'customer' and line_id.location_dest_id.usage == 'internal':
                    return_in_qty += qty
                elif line_id.location_id.usage == 'internal' and line_id.location_dest_id.usage == 'customer':
                    sale_received_qty += qty
                elif line_id.location_id.usage == 'internal' and line_id.location_dest_id.usage == 'inventory':
                    adjustment_out_qty += qty
                elif line_id.location_id.usage == 'internal' and line_id.location_dest_id.usage == 'supplier':
                    return_out_qty += qty
            for move_id in outstanding_sale_move_ids:
                qty = move_id.product_uom._compute_quantity(move_id.product_uom_qty, move_id.product_id.uom_id)
                sale_outstanding_qty += qty
            result.append((
                product_id.barcode or '',
                product_id.name or '',
                product_id.uom_id.name or '',
                round(onhand_qty),
                round(available_qty),
                purchase_qty,
                transfer_in_qty,
                adjustment_in_qty,
                return_in_qty,
                sale_received_qty,
                transfer_out_qty,
                adjustment_out_qty,
                return_out_qty,
                sale_outstanding_qty,
            ))

        column_float_number = {}
        for res in result:
            col = 0
            for column in columns:
                column_name = column[0]
                column_width = column[1]
                column_type = column[2]
                if column_type == 'char':
                    col_value = res[col - 1] if res[col - 1] else ''
                    wbf_value = wbf['content']
                elif column_type == 'no':
                    col_value = no
                    wbf_value = wbf['content']
                else:
                    col_value = res[col - 1] if res[col - 1] else 0
                    if column_type == 'float':
                        wbf_value = wbf['content_float']
                    else:  # number
                        wbf_value = wbf['content_number']
                    column_float_number[col] = column_float_number.get(col, 0) + col_value

                worksheet.write(row - 1, col, col_value, wbf_value)

                col += 1

            row += 1
            no += 1

        worksheet.merge_range('A%s:B%s' % (row, row), 'Grand Total', wbf['total_orange'])
        for x in range(len(columns)):
            if x in (0, 1):
                continue
            column_type = columns[x][3]
            if column_type == 'char':
                worksheet.write(row - 1, x, '', wbf['total_orange'])
            else:
                if column_type == 'float':
                    wbf_value = wbf['total_float_orange']
                else:  # number
                    wbf_value = wbf['total_number_orange']
                if x in column_float_number:
                    worksheet.write(row - 1, x, column_float_number[x], wbf_value)
                else:
                    worksheet.write(row - 1, x, 0, wbf_value)

        worksheet.write('A%s' % (row + 2), 'Date %s (%s)' % (datetime_string, self.env.user.tz or 'Asia/Jakarta'),
                        wbf['content_datetime'])
        workbook.close()
        out = base64.encodebytes(fp.getvalue())
        self.write({'datas': out, 'datas_fname': filename})
        fp.close()
        filename += '%2Exlsx'

        vals = {
            'name': report_name,
            'type': 'binary',
            'datas': out,
            'store_fname': filename,
            'public': True,
        }
        attachment_id = self.env['ir.attachment'].create(vals)

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=ir.attachment&id='+str(attachment_id.id)+'&field=datas&download=true&filename='+filename,
        }

    def send_excel_report(self):
        IrParamSudo = self.env['ir.config_parameter'].sudo()
        web_base_url = IrParamSudo.get_param('web.base.url')
        data = self.print_excel_report()
        user_ids = self.env['res.users'].search([
            ('property_warehouse_id', '=', self.warehouse_id.id)
        ])
        if user_ids:
            email_list = user_ids.filtered(lambda u: u.partner_id.email).mapped('partner_id.email')
            if not self.env.user.company_id.email:
                raise ValidationError(_('Please input company email.'))
            url = requote_uri(web_base_url + '/' + data['url'])
            vals = {
                'subject': 'Daily Stock Movement Report',
                'body_html': f'<a href="{url}">Download Here</a>',
                'attachment_ids': [],
                'email_to': ', '.join(email_list),
                'email_cc': False,
                'auto_delete': False,
                'email_from': self.env.user.company_id.email,
            }
            mail_id = self.env['mail.mail'].sudo().create(vals)
            mail_id.sudo().send()

    def add_workbook_format(self, workbook):
        colors = {
            'white_orange': '#FFFFDB',
            'orange': '#FFC300',
            'red': '#FF0000',
            'yellow': '#F6FA03',
        }

        wbf = {}
        wbf['header'] = workbook.add_format({
            'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 
            'font_color': '#000000', 'font_name': 'Georgia'})
        wbf['header'].set_border()

        wbf['header_orange'] = workbook.add_format({
            'bold': 1, 'align': 'center', 'bg_color': colors['orange'], 'valign': 'vcenter',
            'font_color': '#000000', 'font_name': 'Georgia'})
        wbf['header_orange'].set_border()

        wbf['header_yellow'] = workbook.add_format({
            'bold': 1, 'align': 'center', 'bg_color': colors['yellow'], 'font_color': '#000000', 
            'font_name': 'Georgia'})
        wbf['header_yellow'].set_border()
        
        wbf['header_no'] = workbook.add_format({
            'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 
            'font_name': 'Georgia'})
        wbf['header_no'].set_border()
        wbf['header_no'].set_align('vcenter')
                
        wbf['footer'] = workbook.add_format({'align': 'left', 'font_name': 'Georgia'})
        
        wbf['content_datetime'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss', 'font_name': 'Georgia'})
        wbf['content_datetime'].set_left()
        wbf['content_datetime'].set_right()
        
        wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd', 'font_name': 'Georgia'})
        wbf['content_date'].set_left()
        wbf['content_date'].set_right() 
        
        wbf['title_doc'] = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 20,
            'font_name': 'Georgia',
        })
        
        wbf['company'] = workbook.add_format({'align': 'left', 'font_name': 'Georgia'})
        wbf['company'].set_font_size(11)
        
        wbf['content'] = workbook.add_format()
        wbf['content'].set_left()
        wbf['content'].set_right()

        wbf['content_center'] = workbook.add_format({'align': 'center'})
        wbf['content_center'].set_left()
        wbf['content_center'].set_right()
        
        wbf['content_float'] = workbook.add_format({'align': 'right', 'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['content_float'].set_right() 
        wbf['content_float'].set_left()

        wbf['content_number'] = workbook.add_format({'align': 'right', 'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['content_number'].set_right() 
        wbf['content_number'].set_left() 
        
        wbf['content_percent'] = workbook.add_format({'align': 'right', 'num_format': '0.00%', 'font_name': 'Georgia'})
        wbf['content_percent'].set_right() 
        wbf['content_percent'].set_left() 
                
        wbf['total_float'] = workbook.add_format({
            'bold': 1, 'bg_color': colors['white_orange'], 'align': 'right', 
            'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['total_float'].set_top()
        wbf['total_float'].set_bottom()            
        wbf['total_float'].set_left()
        wbf['total_float'].set_right()         
        
        wbf['total_number'] = workbook.add_format({
            'align': 'right', 'bg_color': colors['white_orange'], 'bold': 1, 
            'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['total_number'].set_top()
        wbf['total_number'].set_bottom()            
        wbf['total_number'].set_left()
        wbf['total_number'].set_right()
        
        wbf['total'] = workbook.add_format({
            'bold': 1, 'bg_color': colors['white_orange'], 'align': 'center', 
            'font_name': 'Georgia'})
        wbf['total'].set_left()
        wbf['total'].set_right()
        wbf['total'].set_top()
        wbf['total'].set_bottom()

        wbf['total_float_yellow'] = workbook.add_format({
            'bold': 1, 'bg_color': colors['yellow'], 'align': 'right', 'num_format': '#,##0', 
            'font_name': 'Georgia'})
        wbf['total_float_yellow'].set_top()
        wbf['total_float_yellow'].set_bottom()
        wbf['total_float_yellow'].set_left()
        wbf['total_float_yellow'].set_right()
        
        wbf['total_number_yellow'] = workbook.add_format({
            'align': 'right', 'bg_color': colors['yellow'], 'bold': 1, 'num_format': '#,##0', 
            'font_name': 'Georgia'})
        wbf['total_number_yellow'].set_top()
        wbf['total_number_yellow'].set_bottom()
        wbf['total_number_yellow'].set_left()
        wbf['total_number_yellow'].set_right()
        
        wbf['total_yellow'] = workbook.add_format({
            'bold': 1, 'bg_color': colors['yellow'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total_yellow'].set_left()
        wbf['total_yellow'].set_right()
        wbf['total_yellow'].set_top()
        wbf['total_yellow'].set_bottom()

        wbf['total_float_orange'] = workbook.add_format({
            'bold': 1, 'bg_color': colors['orange'], 'align': 'right', 'num_format': '#,##0',
            'font_name': 'Georgia'})
        wbf['total_float_orange'].set_top()
        wbf['total_float_orange'].set_bottom()            
        wbf['total_float_orange'].set_left()
        wbf['total_float_orange'].set_right()         
        
        wbf['total_number_orange'] = workbook.add_format({
            'align': 'right', 'bg_color': colors['orange'], 'bold': 1, 'num_format': '#,##0',
            'font_name': 'Georgia'})
        wbf['total_number_orange'].set_top()
        wbf['total_number_orange'].set_bottom()            
        wbf['total_number_orange'].set_left()
        wbf['total_number_orange'].set_right()
        
        wbf['total_orange'] = workbook.add_format({
            'bold': 1, 'bg_color': colors['orange'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total_orange'].set_left()
        wbf['total_orange'].set_right()
        wbf['total_orange'].set_top()
        wbf['total_orange'].set_bottom()
        
        wbf['header_detail_space'] = workbook.add_format({'font_name': 'Georgia'})
        wbf['header_detail_space'].set_left()
        wbf['header_detail_space'].set_right()
        wbf['header_detail_space'].set_top()
        wbf['header_detail_space'].set_bottom()
        
        wbf['header_detail'] = workbook.add_format({'bg_color': '#E0FFC2', 'font_name': 'Georgia'})
        wbf['header_detail'].set_left()
        wbf['header_detail'].set_right()
        wbf['header_detail'].set_top()
        wbf['header_detail'].set_bottom()
        
        return wbf, workbook
