from odoo import models, fields, _
from datetime import datetime
from dateutil import tz
import pandas as pd  # pandas ver. 1.1.5
import binascii
import tempfile
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT


class SaleWizard(models.TransientModel):
    _inherit = 'sale.wizard'

    def mapping_data(self):
        sheet = self.read_file()
        df_head = sheet['df_head']
        df = sheet['df_body']
        vals = []

        for rec in df.index:
            order_line = []
            data_order_line = {}

            # Get data from name column in excel
            data_order = df['Order ID'][rec]
            data_product_sku = df['Stock Keeping Unit (SKU)'][rec]

            # Condition for skip process when value in excel empty
            if data_order == '' or data_product_sku == '':
                continue
            
            # Get data from name column in excel
            duplicated = df.duplicated('Order ID')[rec]
            data_product_name = df['Product Name'][rec]
            data_price = df['Price (Rp.)'][rec]
            data_quantity = df['Quantity'][rec]
            data_disc = df['Discount Amount (Rp.)'][rec]
            data_date = df['Payment Date'][rec]
            data_total = df['Total Amount (Rp.)'][rec]
            data_order_status = df['Order Status'][rec]
            data_invoice_number = df['Invoice'][rec]
            data_product_id = df['Product ID'][rec]
            data_notes = df['Notes'][rec]
            data_shop_name = df_head[0][1]

            data_cust_phone = df['Customer Phone'][rec]
            data_cust_name = df['Customer Name'][rec]
            data_receive_phone = df['Recipient Number'][rec]
            data_receive_name = df['Recipient'][rec]
            data_receive_address = df['Recipient Address'][rec]

            data_courier = df['Courier'][rec]
            data_jenis_layanan = df['Jenis Layanan'][rec]
            data_shipping_price = df['Shipping Price + fee (Rp.)'][rec]
            data_shipping_insurance = df['Insurance (Rp.)'][rec]
            data_shipping_price_total = df['Total Shipping Fee (Rp.)'][rec]
           
            data_awb = df['AWB'][rec]

            
            # Airway Bill condition = True/False
            awb_condition = True if data_awb != '' else False

            # Search Taxes
            taxes_id = self.env['account.tax']\
                .search([('type_tax_use', '=', 'sale'),\
                    ('price_include', '=', True), ('name', 'ilike', 'PPN')])

            # Set Timezone
            date = fields.Datetime.from_string(
                data_date).replace(tzinfo=tz.gettz(self.env.user.tz))
            date = date.astimezone(tz.gettz("UTC"))
            date = date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # Search Sales Team
            team_id = self.env['crm.team'].search([('shop_name', '=', data_shop_name)])
            if len(team_id.ids) > 1:
                name_team = ""
                for rec in team_id:
                    name_team += "\n- %s" %rec.name
                raise ValidationError(_("Please check shop name %s duplicate in sales team!%s") %(data_shop_name, name_team))
            elif len(team_id.ids) == 0:
                raise ValidationError(_("Please check not found shop name %s in sales team!") %(data_shop_name))

            
            # Mapping sale_order Line
            data_order_line = {
                'sku': data_product_sku,
                'product_name': data_product_name,
                'product_id_mkp': data_product_id,
                'product_uom_qty': int(data_quantity),
                'qty_to_invoice': int(data_quantity),
                'price_unit': float(data_price),
                'tax_id': [(6, 0, taxes_id.ids)],
            }

            # Mapping sale_order & Picking
            data_sale_picking = {
                'is_from_excel': True,
                'is_airwaybill_mkp': awb_condition,
                'shop_name': data_shop_name,
                'period': df_head[1][1],
                'farmaku_order_mkp': data_order,
                'invoice_mkp': data_invoice_number,
                'order_status_mkp': data_order_status,
                'date_order': date,
                'partner_id':self.get_customer(data_cust_phone\
                    , data_cust_name, data_receive_phone, data_receive_name, data_receive_address),
                'company_id': 1,  # static value
                'warehouse_id': self.get_warehouse_by_shop_name(data_shop_name),
                'grand_total_price_mkp': float(data_total),
                'notes': data_notes,
                'order_line': order_line,
                'airway_bill': data_awb,
                'shipping_source': 'Marketplace',
                'shipping_name': data_courier,
                'shipping_service_name': data_jenis_layanan,
                'shipping_price': float(data_shipping_price),
                'shipping_insurance': float(data_shipping_insurance),
                'shipping_price_total': float(data_shipping_price_total),
                'team_id': team_id.id,
                'recipient_name': data_receive_name,
                'recipient_phone': data_receive_phone,
                'recipient_address': data_receive_address,
            }

            # Data for create Order line
            # Check condition same order_id and different product_id
            for val in vals:
                total_price = 0
                if str(val['farmaku_order_mkp']) == data_order and duplicated == True:
                    total_price = data_sale_picking['grand_total_price_mkp'] - data_sale_picking['shipping_price_total']
                    val['order_line'].append(data_order_line)
                val['grand_total_price_mkp'] += total_price

            if duplicated == False:
                order_line.append(data_order_line)
                vals.append(data_sale_picking)
            
        return vals