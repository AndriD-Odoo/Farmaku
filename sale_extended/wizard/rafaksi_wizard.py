import pytz
import xlsxwriter
import base64
import logging

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pytz import timezone
from requests.utils import requote_uri

_logger = logging.getLogger(__name__)


class RafaksiWizard(models.TransientModel):
    _name = "rafaksi.wizard"
    _description = "Rafaksi Wizard"
    
    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'Asia/Jakarta'))
    
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    name = fields.Char(
        string='Program Name',
        required=False
    )
    start_date = fields.Date(
        string='Start Date',
        default=fields.Date.today(),
        required=True)
    end_date = fields.Date(
        string='End Date',
        default=fields.Date.today(),
        required=True)
    brand_id = fields.Many2one(
        comodel_name='product.brand',
        string='Brand',
        required=False)
    team_ids = fields.Many2many(
        comodel_name='crm.team',
        string='Sales Team',
        required=False)
    exclude_team_ids = fields.Many2many(
        comodel_name='crm.team',
        relation="rafaksi_wizard_exclude_crm_team_rel",
        column1="rafaksi_wizard_id",
        column2="team_id",
        string='Exclude Sales Team',
        required=False)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=False)
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=False)

    def get_subsidy_amount(self, sale_line_id, so_date, need_qty):
        subsidy_amount = 0
        used_quota = 0
        rafaksi_obj = self.env['rafaksi']
        criteria = [
            ('product_id', '=', sale_line_id.product_id.id),
            '|',
            ('start_date', '<=', so_date),
            ('start_date', '=', False),
            '|',
            ('end_date', '>=', so_date),
            ('end_date', '=', False),
            '|',
            ('current_quota', '>', 0),
            ('quota', '=', 0),  # unlimited
        ]
        if self.name:
            criteria.append(('name', 'ilike', self.name))
        team_ids = self.env['crm.team'].sudo()
        if sale_line_id.order_id.team_id:
            team_ids = self.env['crm.team'].sudo().search([
                ('name', '=', sale_line_id.order_id.team_id.name)
            ])
        rafaksi_id = rafaksi_obj.sudo().search(
            criteria + [('team_ids', 'in', team_ids.ids)],
            order='real_write_date desc',
            limit=1
        )
        if not rafaksi_id:
            rafaksi_id = rafaksi_obj.sudo().search(
                criteria + [
                    ('team_ids', '=', False),
                    ('exclude_team_ids', 'not in', team_ids.ids),
                ], order='real_write_date desc', limit=1
            )
        if rafaksi_id:
            subsidy_amount = rafaksi_id.subsidy_amount
            used_quota = min(rafaksi_id.current_quota, need_qty)
            rafaksi_id.current_quota -= used_quota
        return rafaksi_id, subsidy_amount, used_quota

    def print_excel_report(self):
        # reset quota dulu
        query = """
            UPDATE
                rafaksi
            SET
                current_quota = quota
        """
        self.env.cr.execute(query=query)
        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        report_name = 'Report Rafaksi'
        filename = '%s %s' % (report_name, date_string)

        columns = [
            ('No', 5, 'no', 'no'),
            ('Program Name', 20, 'char', 'char'),
            ('SO', 20, 'char', 'char'),
            ('SO Date', 20, 'char', 'char'),
            ('Sales Team', 20, 'char', 'char'),
            ('Warehouse', 20, 'char', 'char'),
            ('Product', 40, 'char', 'char'),
            ('Qty Sold', 20, 'float', 'float'),
            ('UoM', 20, 'char', 'char'),
            ('Sales Price', 20, 'float', 'float'),
            ('Subtotal Sold', 20, 'float', 'float'),
            ('Rafaksi Amount', 20, 'float', 'float'),
            ('Total Rafaksi Amount', 25, 'float', 'float'),
        ]

        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:K3', report_name, wbf['title_doc'])

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

        criteria = [
            ('order_id.state', 'in', ['sale', 'done']),
            ('qty_delivered', '>', 0),
        ]
        if self.start_date:
            start_date = self.start_date.strftime('%Y-%m-%d 00:00:00')
            start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
            start_date = pytz.timezone(self.env.user.tz or 'Asia/Jakarta').localize(start_date).astimezone(pytz.UTC)
            start_date = start_date.strftime('%Y-%m-%d %H:%M:%S')
            criteria += [
                ('order_id.date_order', '>=', start_date)
            ]
        if self.end_date:
            end_date = self.end_date.strftime('%Y-%m-%d 23:59:59')
            end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
            end_date = pytz.timezone(self.env.user.tz or 'Asia/Jakarta').localize(end_date).astimezone(pytz.UTC)
            end_date = end_date.strftime('%Y-%m-%d %H:%M:%S')
            criteria += [
                ('order_id.date_order', '<=', end_date)
            ]
        if self.brand_id:
            criteria += [
                ('product_id.brand_id', '=', self.brand_id.id)
            ]
        if self.product_id:
            criteria += [
                ('product_id', '=', self.product_id.id)
            ]
        if self.warehouse_id:
            criteria += [
                ('order_id.warehouse_id', '=', self.warehouse_id.id)
            ]
        if self.team_ids:
            criteria += [
                ('order_id.team_id.id', 'in', self.team_ids.ids)
            ]
        if self.exclude_team_ids:
            criteria += [
                ('order_id.team_id.id', 'not in', self.exclude_team_ids.ids)
            ]
        _logger.info(f'\ncriteria rafaksi: {criteria}')
        rec_ids = self.env['sale.order.line'].search(criteria, order='id asc')
        total_used_quota = 0
        total_sold_amount = 0
        total_subsidy_amount = 0
        grand_total_subsidy_amount = 0
        for rec_id in rec_ids:
            so_date = ''
            if rec_id.order_id.date_order:
                date_order_tz = pytz.UTC.localize(rec_id.order_id.date_order).astimezone(timezone(
                    self.env.user.tz or 'Asia/Jakarta'))
                so_date = date_order_tz.date()
                so_date = fields.Date.to_string(so_date)
            need_qty = rec_id.product_uom._compute_quantity(
                rec_id.product_qty,
                rec_id.product_id.uom_id
            )
            subsidy_amount = True
            while need_qty and subsidy_amount:
                rafaksi_id, subsidy_amount, used_quota = self.get_subsidy_amount(
                    sale_line_id=rec_id,
                    so_date=so_date,
                    need_qty=need_qty
                )
                if not subsidy_amount:
                    break
                need_qty -= used_quota
                used_quota_uom = rec_id.product_id.uom_id._compute_quantity(
                    used_quota or need_qty,
                    rec_id.product_uom
                )
                worksheet.write(row, 0, no, wbf['content_no'])
                worksheet.write(row, 1, rafaksi_id.name or '', wbf['content'])
                worksheet.write(row, 2, rec_id.order_id.name or '', wbf['content'])
                worksheet.write(row, 3, so_date, wbf['content'])
                worksheet.write(row, 4, rec_id.order_id.team_id.name or '', wbf['content'])
                worksheet.write(row, 5, rec_id.order_id.warehouse_id.name or '', wbf['content'])
                worksheet.write(row, 6, rec_id.product_id.display_name, wbf['content'])
                worksheet.write(row, 7, used_quota_uom, wbf['content_number'])
                worksheet.write(row, 8, rec_id.product_uom.name, wbf['content'])
                worksheet.write(row, 9, rec_id.price_unit, wbf['content_float'])
                worksheet.write(row, 10, used_quota_uom * rec_id.price_unit, wbf['content_float'])
                worksheet.write(row, 11, subsidy_amount, wbf['content_float'])
                worksheet.write(row, 12, subsidy_amount * used_quota_uom, wbf['content_float'])
                total_sold_amount += (used_quota_uom * rec_id.price_unit)
                total_used_quota += used_quota_uom
                total_subsidy_amount += subsidy_amount
                grand_total_subsidy_amount += (subsidy_amount * used_quota_uom)
                # break loop jika sudah tidak ada used quota
                if not used_quota:
                    need_qty = 0
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
        worksheet.write(row, 7, total_used_quota, wbf['total_number_orange'])
        worksheet.write(row, 8, '', wbf['total_orange'])
        worksheet.write(row, 9, '', wbf['total_orange'])
        worksheet.write(row, 10, total_sold_amount, wbf['total_float_orange'])
        worksheet.write(row, 11, total_subsidy_amount, wbf['total_float_orange'])
        worksheet.write(row, 12, grand_total_subsidy_amount, wbf['total_float_orange'])
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
            {'bold': 1, 'bg_color': colors['orange'], 'align': 'center', 'font_name': 'Arial',
             'num_format': '#,##0.00'})
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
