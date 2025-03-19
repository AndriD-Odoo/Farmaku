from odoo import models
from xlsxwriter.utility import xl_rowcol_to_cell

columns = [
    ['Product Name', 50, 'normal_date'],
    ['Product Code', 30, 'normal'],
    ['Barcode', 30, 'normal'],
    ['Unit Price', 20, 'normal'],
    ['Stock', 10, 'normal'],
    ['Mapped', 10, 'normal'],
]

class ReportOrder(models.AbstractModel):
    _name = 'report.asb_rest_api.order'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'XLSX Order Report'

    def generate_xlsx_report(self, wb, data, objects, style):
        if '-' not in data:
            data = objects.get_order_report()
        
        ws = wb.add_worksheet('Order Info')
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0
        ws.fit_width_to_pages = 1
        ws.freeze_panes(6, 0)

        ws.merge_range(0, 0, 0, 5, 'Order Info - ' +
                       objects.env.company.name, style['normal_bold'])
        
        if data:
            row_count = 2
            ws.write(row_count, 0, 'Order Status', style['blue_center'])
            ws.write(row_count, 1, 'Order Number', style['blue_center'])
            ws.write(row_count, 2, 'Invoice Number', style['blue_center'])
            ws.write(row_count, 3, 'Grand Total Price', style['blue_center'])
            ws.write(row_count, 4, 'Order Date', style['blue_center'])
            ws.write(row_count, 5, 'Has Concoction', style['blue_center'])
            ws.write(row_count, 6, 'Pharmacy Code', style['blue_center'])

            ws.write(row_count, 7, 'Airway Bill', style['blue_center'])
            ws.write(row_count, 8, 'Address', style['blue_center'])
            ws.write(row_count, 9, 'Longitude', style['blue_center'])
            ws.write(row_count, 10, 'Latitude', style['blue_center'])
            ws.write(row_count, 11, 'Shipping Distance', style['blue_center'])
            ws.write(row_count, 12, 'Shipping Note', style['blue_center'])
            ws.write(row_count, 13, 'Shipping Name', style['blue_center'])
            ws.write(row_count, 14, 'Shipping Service Name', style['blue_center'])

            ws.write(row_count, 15, 'Delivery Status', style['blue_center'])
            ws.write(row_count, 16, 'Driver Name', style['blue_center'])
            ws.write(row_count, 17, 'Driver Phone', style['blue_center'])
            ws.write(row_count, 18, 'Driver Photo Url Path', style['blue_center'])
            ws.write(row_count, 19, 'Driver Plat Number', style['blue_center'])
            ws.write(row_count, 20, 'Driver Vehicle Number', style['blue_center'])
            ws.write(row_count, 21, 'Tracking Url', style['blue_center'])

            ws.write(row_count, 22, 'Name', style['blue_center'])
            ws.write(row_count, 23, 'Phone', style['blue_center'])
            ws.write(row_count, 24, 'Gender', style['blue_center'])
            ws.write(row_count, 25, 'Date of Birth', style['blue_center'])

            row_count += 1
            ws.write(row_count, 0, data.get('orderStatus',''), style['normal_center'])
            ws.write(row_count, 1, data.get('orderNumber',''), style['normal_center'])
            ws.write(row_count, 2, data.get('invoiceNumber',''), style['normal_center'])
            ws.write(row_count, 3, data.get('grandTotalPrice',''), style['normal_center'])
            ws.write(row_count, 4, data.get('orderDate',''), style['normal_center'])
            ws.write(row_count, 5, data.get('hasConcoction',''), style['normal_center'])
            ws.write(row_count, 6, data.get('pharmacyCode',''), style['normal_center'])
            ws.write(row_count, 7, data['delivery']['airwayBill'], style['normal_center'])
            ws.write(row_count, 8, data['delivery']['address'], style['normal_center'])
            ws.write(row_count, 9, data['delivery']['longitude'], style['normal_center'])
            ws.write(row_count, 10, data['delivery']['latitude'], style['normal_center'])
            ws.write(row_count, 11, data['delivery']['shippingDistance'], style['normal_center'])
            ws.write(row_count, 12, data['delivery']['shippingNote'], style['normal_center'])
            ws.write(row_count, 13, data['delivery']['shippingName'], style['normal_center'])
            ws.write(row_count, 14, data['delivery']['shippingServiceName'], style['normal_center'])
            ws.write(row_count, 15, data['delivery']['deliveryStatus'], style['normal_center'])
            ws.write(row_count, 16, data['delivery']['driverName'], style['normal_center'])
            ws.write(row_count, 17, data['delivery']['driverPhone'], style['normal_center'])
            ws.write(row_count, 18, data['delivery']['driverPhotoUrlPath'], style['normal_center'])
            ws.write(row_count, 19, data['delivery']['driverPlateNumber'], style['normal_center'])
            ws.write(row_count, 20, data['delivery']['driverVehicleModel'], style['normal_center'])
            ws.write(row_count, 21, data['delivery']['trackingUrl'], style['normal_center'])
            ws.write(row_count, 22, data['customer']['name'], style['normal_center'])
            ws.write(row_count, 23, data['customer']['phone'], style['normal_center'])
            ws.write(row_count, 24, data['customer']['gender'], style['normal_center'])
            ws.write(row_count, 25, data['customer']['dateOfBirth'], style['normal_center'])
