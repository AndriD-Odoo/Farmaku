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


class NearExpiredDateWizard(models.TransientModel):
    _name = "near.expired.date.wizard"
    _description = "Near Expired Date Wizard .xlsx"
    
    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))

    def _default_start_date(self):
        return fields.Date.today().strftime('%Y-%m-01')
    
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    name = fields.Char(
        string='Name',
        default='Near expired date in 4 months and between 4 to 7 months.')

    def print_excel_report(self):
        datetime_format = '%Y-%m-%d %H:%M:%S'
        utc = datetime.now().strftime(datetime_format)
        utc = datetime.strptime(utc, datetime_format)
        tz = self.get_default_date_model().strftime(datetime_format)
        tz = datetime.strptime(tz, datetime_format)
        duration = tz - utc
        hours = duration.seconds / 60 / 60

        months_ago_4 = tz + relativedelta(months=4)
        months_ago_7 = tz + relativedelta(months=7)
        domain_4_months = [
            ('expiration_date', '>=', datetime.now()),
            ('expiration_date', '<=', months_ago_4),
        ]
        domain_4_7_months = [
            ('expiration_date', '>=', datetime.now()),
            ('expiration_date', '>', months_ago_4),
            ('expiration_date', '<=', months_ago_7),
        ]
        domains = [domain_4_months, domain_4_7_months]
        obj_serial_number = self.env['stock.production.lot']

        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        report_name = 'Near Expired Date'
        filename = '%s %s' % (report_name, date_string)

        columns = [
            ('No', 5, 'no', 'no'),
            ('Internal Reference', 20, 'char', 'char'),
            ('Barcode', 20, 'char', 'char'),
            ('Product', 30, 'char', 'char'),
            ('Lot/Serial Number', 30, 'char', 'char'),
            ('Quantity', 20, 'float', 'float'),
            ('UoM', 20, 'char', 'char'),
            ('Purchase UoM', 20, 'char', 'char'),
            ('Expiration Date', 20, 'datetime', 'char'),
            ('Vendor', 30, 'char', 'char'),
            ('Vendor Return Type', 30, 'char', 'char'),
            ('No. Reference PO', 30, 'char', 'char'),
            ('No. Reference Outstanding PO', 30, 'char', 'char'),
            ('Qty Outstanding PO', 30, 'char', 'char'),
        ]

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)

        SHEET_NAMES = [
            'Near Expired Date in 4 Months',
            'Near Expired Date Between 4 to 7 Months',
        ]
        index = 0
        for domain in domains:
            lot_ids = obj_serial_number.search(domain)
            wbf, workbook = self.add_workbook_format(workbook)

            worksheet = workbook.add_worksheet(SHEET_NAMES[index])
            worksheet.merge_range('A2:N3', SHEET_NAMES[index], wbf['title_doc'])
            index += 1

            row = 5

            col = 0
            for column in columns:
                column_name = column[0]
                column_width = column[1]
                worksheet.set_column(col, col, column_width)
                worksheet.write(row-1, col, column_name, wbf['header_orange'])

                col += 1

            row += 1
            no = 1

            result = []
            for lot_id in lot_ids:
                po = []
                po_outstanding = []
                purchase_uom = []
                vendor = []
                vendor_return_type = []
                qty_outstanding = []
                order_lines = self.env['purchase.order.line'].search([
                    ('product_id', '=', lot_id.product_id.id),
                    ('order_id.state', '!=', 'cancel'),
                    ('order_id', 'in', lot_id.purchase_order_ids.ids)
                ])
                for line_id in order_lines:
                    if line_id.order_id.name not in po:
                        po.append(line_id.order_id.name)
                    if line_id.order_id.partner_id.name not in vendor:
                        vendor.append(line_id.order_id.partner_id.name)
                    if line_id.order_id.partner_id.purchase_return_type_id.name:
                        vendor_return_type.append(line_id.order_id.partner_id.purchase_return_type_id.name)
                    purchase_uom.append(line_id.product_uom.name)
                    outstanding_picking_ids = line_id.order_id.picking_ids.filtered(
                        lambda p: p.location_id.usage == 'supplier' and p.state in ['confirmed', 'assigned'])
                    if line_id.qty_received < line_id.product_qty and outstanding_picking_ids:
                        if line_id.order_id.name not in po_outstanding:
                            po_outstanding.append(line_id.order_id.name)
                        qty_outstanding.append(str(int(line_id.product_qty - line_id.qty_received)))
                purchase_uom = ', '.join(purchase_uom)
                vendor = ', '.join(vendor)
                vendor_return_type = ', '.join(vendor_return_type)
                reference_po = ', '.join(po)
                reference_po_outstanding = ', '.join(po_outstanding)
                qty_po_outstanding = ', '.join(qty_outstanding)
                result.append((
                    lot_id.product_id.default_code,
                    lot_id.product_id.barcode,
                    lot_id.product_id.name,
                    lot_id.name,
                    lot_id.product_qty,
                    lot_id.product_uom_id.name,
                    purchase_uom,
                    lot_id.expiration_date + relativedelta(hours=hours),
                    vendor,
                    vendor_return_type,
                    reference_po,
                    reference_po_outstanding,
                    qty_po_outstanding
                ))

            column_float_number = {}
            for res in result:
                col = 0
                for column in columns:
                    column_type = column[2]
                    if column_type == 'char':
                        col_value = res[col-1] if res[col-1] else ''
                        wbf_value = wbf['content']
                    elif column_type == 'no':
                        col_value = no
                        wbf_value = wbf['content_center']
                    elif column_type == 'datetime':
                        col_value = res[col - 1].strftime(datetime_format) if res[col - 1] else ''
                        wbf_value = wbf['content']
                    else:
                        col_value = res[col-1] if res[col-1] else 0
                        if column_type == 'float':
                            wbf_value = wbf['content_float']
                        else:  # number
                            wbf_value = wbf['content_number']
                        column_float_number[col] = column_float_number.get(col, 0) + col_value

                    worksheet.write(row-1, col, col_value, wbf_value)

                    col += 1

                row += 1
                no += 1

            worksheet.merge_range('A%s:B%s' % (row, row), 'Grand Total', wbf['total_orange'])
            for x in range(len(columns)):
                if x in (0, 1):
                    continue
                column_type = columns[x][3]
                if column_type == 'char':
                    worksheet.write(row-1, x, '', wbf['total_orange'])
                else:
                    if column_type == 'float':
                        wbf_value = wbf['total_float_orange']
                    else:  # number
                        wbf_value = wbf['total_number_orange']
                    if x in column_float_number:
                        worksheet.write(row-1, x, column_float_number[x], wbf_value)
                    else:
                        worksheet.write(row-1, x, 0, wbf_value)

            worksheet.write('A%s' % (row+2), 'Date %s (%s)' % (datetime_string,self.env.user.tz or 'Asia/Jakarta'), wbf['content_datetime'])
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
        param_id = self.sudo().env.ref('product_expiry_extended.ir_config_parameter_near_expired_email')
        if not param_id.value:
            raise ValidationError(_('Please input email in system parameter "product_expiry_extended.near_expired_email"'))
        if not self.env.user.company_id.email:
            raise ValidationError(_('Please input company email.'))
        url = requote_uri(web_base_url + '/' + data['url'])
        vals = {
            'subject': 'Near Expired Date Serial Number',
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
            'bold': 1, 'align': 'center', 'bg_color': colors['orange'], 
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
