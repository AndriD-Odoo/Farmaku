from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pytz import timezone
from requests.utils import requote_uri
import pytz
import xlsxwriter
import base64


class StockReportWizard(models.TransientModel):
    _name = "stock.report.wizard"
    _description = "Daily Stock Report Wizard .xlsx"
    
    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))
    
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)

    def print_excel_report(self):
        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        report_name = 'Daily Stock Report'
        filename = '%s %s' % (report_name, date_string)

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)

        wbf, workbook = self.add_workbook_format(workbook)
        company_ids = self.env['res.company'].search([])
        for company_id in company_ids:
            warehouse_ids = self.env['stock.warehouse'].search([
                ('company_id', '=', company_id.id)
            ])
            if not warehouse_ids:
                continue
            location_ids = warehouse_ids.mapped('lot_stock_id')
            quants = self.env['stock.quant'].search([
                ('location_id', 'in', location_ids.ids)
            ])
            product_dict = {}
            for quant in quants:
                product_dict.setdefault(quant.product_id, {})
                list_location = product_dict[quant.product_id].get(quant.location_id, [0, 0])
                qty = list_location[0] + quant.available_quantity
                value = list_location[1] + quant.value
                product_dict[quant.product_id][quant.location_id] = [qty, value]
            quant_product = product_dict.keys()
            quant_product = [prod.id for prod in quant_product]
            additional_product = self.env['product.product'].search(
                [('id', 'not in', quant_product), ('type', '=', 'product')])
            for add_prod in additional_product:
                product_dict[add_prod] = {}
            columns = []
            for location in location_ids:
                columns += [(location.complete_name, 15, location.id),
                            (location.location_id.name + '/Value', 15, location.id)]
            worksheet = workbook.add_worksheet(company_id.display_name)
            worksheet.set_column('A3:A3', 25)
            worksheet.set_column('B3:B3', 60)
            worksheet.merge_range('A1:B2', 'Daily Stock Report', wbf['title_doc'])

            col = 2
            row = 3
            worksheet.merge_range('A4:A5', 'Barcode', wbf['header_orange'])
            worksheet.merge_range('B4:B5', 'Name', wbf['header_orange'])
            worksheet.merge_range(row, col, row, (len(columns) + 1), 'Location Stock', wbf['header_orange'])
            row += 1
            for column in columns:
                column_name = column[0]
                column_width = column[1]
                worksheet.set_column(col, col, column_width)
                worksheet.write(row, col, column_name, wbf['header_orange'])
                col += 1
            row += 1
            worksheet.freeze_panes(row, 2)
            column_number = {}
            for product, locations in product_dict.items():
                worksheet.write(row, 0, product.barcode or '', wbf['content'])
                worksheet.write(row, 1, product.name, wbf['content'])
                col = 2
                for loc in location_ids:
                    loc_exist = []
                    if locations:
                        loc_vals = locations.keys()
                        if loc in loc_vals:
                            vals = locations.get(loc, False)
                            if vals:
                                # isi qty
                                col_value = int(vals[0])
                                wbf_value = wbf['content_number']
                                worksheet.write(row, col, col_value, wbf_value)
                                column_number[col] = column_number.get(col, 0) + col_value
                                col += 1
                                # isi value
                                col_value = vals[1]
                                wbf_value = wbf['content_float']
                                worksheet.write(row, col, col_value, wbf_value)
                                column_number[col] = column_number.get(col, 0) + col_value
                                col += 1
                        else:
                            worksheet.write(row, col, '', wbf['content'])
                            col += 1
                            worksheet.write(row, col, '', wbf['content'])
                            col += 1
                            loc_exist.append(loc.id)
                    else:
                        worksheet.write(row, col, '', wbf['content'])
                        col += 1
                        worksheet.write(row, col, '', wbf['content'])
                        col += 1
                row += 1
            worksheet.merge_range('A%s:B%s' % (row, row), 'Total', wbf['total_orange'])
            for x in range(len(columns) + 2):
                if x in (0, 1):
                    continue
                wbf_value = wbf['total_number_orange']
                if x in column_number:
                    worksheet.write(row - 1, x, column_number[x], wbf_value)
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
        param_id = self.sudo().env.ref('stock_extended.ir_config_parameter_stock_report_email')
        if not param_id.value:
            raise ValidationError(_('Please input email in system parameter "stock_extended.stock_report_email"'))
        if not self.env.user.company_id.email:
            raise ValidationError(_('Please input company email.'))
        url = requote_uri(web_base_url + '/' + data['url'])
        vals = {
            'subject': 'Daily Stock Report',
            'body_html': f'<a href="{url}">Download Here</a>',
            'attachment_ids': [],
            'email_to': param_id.value,
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
        
        wbf['content_float'] = workbook.add_format({'align': 'right', 'num_format': '#,##0.00', 'font_name': 'Georgia'})
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
            'num_format': '#,##0.00', 'font_name': 'Georgia'})
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
            'bold': 1, 'bg_color': colors['yellow'], 'align': 'right', 'num_format': '#,##0.00', 
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
            'bold': 1, 'bg_color': colors['orange'], 'align': 'right', 'num_format': '#,##0.00',
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
