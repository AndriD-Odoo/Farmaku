from odoo import models
from io import BytesIO

import logging
_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.warning('Can not import xlsxwriter`.')


class ReportXlsxAbstract(models.AbstractModel):
    _inherit = 'report.report_xlsx.abstract'

    def xlsx_style(self, wb):
        res = {
            'title': wb.add_format({'bold': True, 'border': True, 'align': 'center', 'text_wrap': True}),
            'title_financial': wb.add_format({'font_color': '#16365c', 'font_size': '28', 'bold': True, 'border': True, 'align': 'center', 'text_wrap': True}),
            'title_table': wb.add_format({'bg_color': '#1f497d', 'font_color': '#ffffff', 'bold': True, 'border': True, 'align': 'center', 'text_wrap': True}),
            'blue': wb.add_format({'bg_color': '#ccffff', 'bold': True, 'border': True, 'num_format': '#,##0'}),
            'blue_percent': wb.add_format({'bg_color': '#ccffff', 'bold': True, 'border': True, 'num_format': '0.0%'}),
            'blue_center': wb.add_format({'bg_color': '#ccffff', 'align': 'center', 'bold': True, 'border': True}),
            'blue_right': wb.add_format({'bg_color': '#ccffff', 'align': 'right', 'bold': True, 'border': True, 'num_format': '#,##0'}),
            'blue_center_font': wb.add_format({'bg_color': '#ccffff', 'font_color': '#0000FF', 'align': 'center', 'bold': True, 'border': True}),
            'blue_right_font': wb.add_format({'bg_color': '#ccffff', 'font_color': '#0000FF', 'align': 'right', 'num_format': '#,##0', 'bold': True, 'border': True}),
            'yellow': wb.add_format({'bg_color': '#ffffcc', 'bold': True, 'border': True, 'num_format': '#,##0'}),
            'yellow_center': wb.add_format({'bg_color': '#ffffcc', 'align': 'center', 'bold': True, 'border': True}),
            'yellow_right': wb.add_format({'bg_color': '#ffffcc', 'align': 'right', 'bold': True, 'border': True, 'num_format': '#,##0'}),
            'yellow_percent': wb.add_format({'bg_color': '#ffffcc', 'bold': True, 'border': True, 'num_format': '0.0%'}),
            'grey': wb.add_format({'bg_color': '#c0c0c0', 'bold': True, 'border': True, 'num_format': '#,##0'}),
            'normal': wb.add_format({'border': True, 'num_format': '#,##0', 'text_wrap': True}),
            'normal_bold_right': wb.add_format({'border': True, 'num_format': '#,##0', 'bold': True, 'align': 'right'}),
            'normal_bold_right_no_border': wb.add_format({'num_format': '#,##0.00', 'bold': True, 'align': 'right'}),
            'normal_bold_center': wb.add_format({'border': True, 'num_format': '#,##0', 'bold': True, 'align': 'center'}),
            'normal_bold_center_gray': wb.add_format({'border': True, 'num_format': '#,##0', 'bold': True, 'align': 'center', 'bg_color': '#c0c0c0'}),
            'normal_bold_right_gray': wb.add_format({'border': True, 'num_format': '"Rp"   #,##0', 'bold': True, 'align': 'right', 'bg_color': '#c0c0c0'}),
            'normal_red': wb.add_format({'border': True, 'num_format': '#,##0', 'bg_color': 'red', 'font_color': 'white'}),
            'normal_red_percent': wb.add_format({'border': True, 'num_format': '0.00%', 'bg_color': 'red', 'font_color': 'white'}),
            'normal_font_red': wb.add_format({'border': True, 'num_format': '#,##0', 'bold': True, 'font_color': 'red'}),
            'normal_font_red_percent': wb.add_format({'border': True, 'num_format': '0.00%', 'bold': True, 'font_color': 'red'}),
            'blue_font_red': wb.add_format({'bg_color': '#ccffff', 'bold': True, 'border': True, 'num_format': '#,##0', 'font_color': 'red'}),
            'blue_font_red_percent': wb.add_format({'bg_color': '#ccffff', 'bold': True, 'border': True, 'num_format': '0.00%', 'font_color': 'red'}),
            'normal_bold': wb.add_format({'bold': True, 'border': True, 'num_format': '#,##0'}),
            'bold': wb.add_format({'bold': True}),
            'normal_date': wb.add_format({'num_format': 'dd/mm/yy', 'border': True}),
            'normal_center': wb.add_format({'align': 'center', 'border': True, 'text_wrap': True, 'num_format': '#,##0'}),
            'center': wb.add_format({'align': 'center'}),
            'right': wb.add_format({'align': 'right'}),
            'normal_italic': wb.add_format({'italic': True, 'border': True}),
            'normal_percent': wb.add_format({'num_format': '0.00%', 'border': True}),
            'normal_percent_center': wb.add_format({'align': 'center', 'num_format': '0.00%', 'border': True}),
            'normal_percent_bold': wb.add_format({'num_format': '0.0%', 'bold': True, 'border': True}),
            'normal_number_right': wb.add_format({'num_format': '#,##0', 'align': 'right'}),
            'normal_number_right_add_zero': wb.add_format({'num_format': '#,##0.00', 'align': 'right'}),
            'index': wb.add_format({'num_format': '#', 'align': 'center', 'border': True}),
        }
        res['yellow_center'].set_align('vcenter')
        res['normal_center'].set_align('vcenter')
        res['normal_percent_center'].set_align('vcenter')
        res['blue_center'].set_align('vcenter')
        return res

    def create_xlsx_report(self, docids, data):
        objs = self.env[self.env.context.get('active_model')].browse(docids)
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data, self.get_workbook_options())
        self.generate_xlsx_report(
            workbook, data, objs, self.xlsx_style(workbook))
        workbook.close()
        file_data.seek(0)
        return file_data.read(), 'xlsx'

    def get_workbook_options(self):
        return {}

    def generate_xlsx_report(self, workbook, data, objs, style):
        raise NotImplementedError()
