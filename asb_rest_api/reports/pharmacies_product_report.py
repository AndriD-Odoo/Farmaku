from odoo import models
from xlsxwriter.utility import xl_rowcol_to_cell

columns = [
    ['Pharmacy Code', 30, 'normal'],
    ['Pharmacy Name', 30, 'normal'],
    ['Product Code', 30, 'normal'],
    ['Product Name', 65, 'normal_date'],
    ['Barcode', 30, 'normal'],
    ['Unit Price', 20, 'normal'],
    ['Stock', 10, 'normal'],
    ['Mapped', 10, 'normal'],
]

class ReportPharmaciesProduct(models.AbstractModel):
    _name = 'report.asb_rest_api.pharmacies_product'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'XLSX Pharmacies Product Report'

    def generate_xlsx_report(self, wb, data, objects, style):
        if '-' not in data:
            data = objects.get_product_report()
        
        ws = wb.add_worksheet('Pharmacies Product')
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0
        ws.fit_width_to_pages = 1
        ws.freeze_panes(3, 0)

        ws.merge_range(0, 0, 0, 5, 'Pharmacies Product - ' +
                       objects.env.company.name, style['normal_bold'])
        
        if data:
            row_count = 2
            col_count = 0

            for column in columns:
                ws.set_column(col_count, col_count, column[1])
                ws.write(row_count, col_count, column[0], style['yellow_center'])
                col_count += 1

            row_count += 1
            for data in data.get('data'):
                col_count = 0
                ws.write(row_count, col_count, data['pharmacyCode'], style['normal_center'])
                col_count += 1
                ws.write(row_count, col_count, data['pharmacyName'], style['normal_center'])
                col_count += 1
                ws.write(row_count, col_count, data['productCode'], style['normal_center'])
                col_count += 1
                ws.write(row_count, col_count, data['productName'], style['normal_center'])
                col_count += 1
                ws.write(row_count, col_count, data['barcode'], style['normal_center'])
                col_count += 1
                ws.write(row_count, col_count, data['unitPrice'], style['normal_center'])
                col_count += 1
                ws.write(row_count, col_count, data['stock'], style['normal_center'])
                col_count += 1
                ws.write(row_count, col_count, data['isMapped'], style['normal_center'])
                row_count += 1            
