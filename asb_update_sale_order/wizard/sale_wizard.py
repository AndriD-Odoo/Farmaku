from odoo import models, fields, _
from datetime import datetime
from dateutil import tz
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import pandas as pd  # pandas ver. 1.1.5
import binascii
import tempfile
import pytz


class SaleWizard(models.TransientModel):
    _name = 'sale.wizard'
    _description = 'Sale Wizard'

    name = fields.Char()
    upload_file = fields.Binary(string='Upload File', attachment=False)

    def read_file(self):
        if self.upload_file:
            fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.upload_file))  # Encode binary file to xlsx
            fp.seek(0)
            head = pd.read_excel(open(fp.name, 'rb'), 0, engine='openpyxl', header=None, na_filter=False, na_values=None)
            body = pd.read_excel(open(fp.name, 'rb'), 0, engine='openpyxl', header=3, na_filter=False, na_values=None)  # Open file xlsx with pandas
            body.fillna('')  # Default cell value
            df_head = pd.DataFrame(head.head(2).T.head(2), index=[1])
            df = pd.DataFrame(body)
            df = df.astype(str)
            return {
                'df_head': df_head,
                'df_body': df
            }
        else:
            raise UserError(_("Please Upload a File"))

    def get_customer(self, cust_phone, cust_name, receive_phone, receive_name, receive_address):
        partner_id = self.env['res.partner']
        customer = partner_id.search(['|', ('phone', '=', str(int(cust_phone))), ('mobile', '=', str(int(cust_phone)))], limit=1)
        if len(customer) > 1:
            raise UserError(_("There are customers with same phone/mobile number (%s)" % (','.join([cust.name for cust in customer]),)))
        if customer:
            result = customer.id
        else:
            child_ids = []
            if cust_phone != receive_phone:
                data_child_ids = {
                    'type': 'delivery',
                    'name': str(receive_name),
                    'phone': str(receive_phone),
                    'mobile': str(receive_phone),
                    'street': str(receive_address),
                }
                child_ids.append((0, 0, data_child_ids))
            res = partner_id.create([{
                'name': str(cust_name),
                'phone': str(cust_phone),
                'mobile': str(cust_phone),
                'child_ids': child_ids
            }])
            if cust_phone == receive_phone:
                res['street'] = str(receive_address)
            result = res.id
        return result

    def get_warehouse_by_shop_name(self, shop_name):
        # Search Warehouse by shop name
        shop_name_id = self.env['shop.name.conf'].search([('name', '=', shop_name)])
        if len(shop_name_id.ids) == 1:
            warehouse_id = shop_name_id.warehouse_id
        else:
            raise UserError('Shop name more than one or none. Please check shop name configuration !')
        return warehouse_id.id

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

    def button_bulk_create(self):
        vals = self.mapping_data()
        meta = {
            'count_success': 0,
            'count_fail': 0,
            'notif_import_line': [(5,0,0)],
        }

        for rec in vals:
            # Check order status
            sale_order, meta, type_status = self.check_status_mkp(rec, meta)
            if type_status == False:
                continue

            # Check Product Available and Stock Product
            sale_order, meta = self.check_product(sale_order, meta)
            if len(sale_order) == 0:
                continue 

            sale_id = self.env['sale.order'].search([('farmaku_order_mkp', '=', sale_order['farmaku_order_mkp'])])\
                if sale_order else False
            if self.check_status(sale_id.order_status_mkp) == 'done':
                continue
            sale_order = self.prepare_fields(rec, 'sale.order')
            
            try:
                # Create / Write Sale Order
                if not sale_id:
                    sale_id = sale_id.sudo().create(sale_order)
                else:
                    sale_id.sudo().write({
                        'order_status_mkp': sale_order['order_status_mkp'],
                    })
            except:
                meta['notif_import_line'].append((0,0,{
                    'order': rec['farmaku_order_mkp'],
                    'sku': '',
                    'product_name': '',
                    'status': '',
                    'reason': "Failed to Create/Update Order",
                }))
                count_order_line = len(rec['order_line'])
                meta['count_success'] -= count_order_line
                meta['count_fail'] += count_order_line
                continue

            self.execute_process_by_status(rec, sale_id, type_status)
            
        context = {
            'default_name': self.name,
            'default_count_success': meta['count_success'],
            'default_count_fail': meta['count_fail'],
            'default_notif_import_line': meta['notif_import_line'],
            'default_warehouse_id': vals[0]['warehouse_id'],
        }
        
        view_id = self.env.ref('asb_update_sale_order.sale_order_view_form_import').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bulk Import Sale Order'),
            'res_model': 'notif.import',
            'target': 'new',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'context': context
        }
    
    def act_validate_picking(self, sale):
        if sale.picking_ids.state != 'done':
            sale.picking_ids.move_line_ids_without_package['qty_done'] = sale.order_line.product_uom_qty
            sale.picking_ids.button_validate()
    
    def act_create_invoice(self, sale):
        invoice = sale.env["sale.advance.payment.inv"].create({})
        invoice.with_context(active_ids=sale.ids).create_invoices()
        user_tz = self.env.user.tz or 'Asia/Jakarta'
        invoice_date = False
        if sale.date_order:
            invoice_date = pytz.UTC.localize(sale.date_order).astimezone(pytz.timezone(user_tz))
        sale.invoice_ids.write({
            'invoice_date': invoice_date,
            'sale_id': sale.id,
            'is_from_excel': sale.is_from_excel,
            'farmaku_order_mkp': sale.farmaku_order_mkp,
            'invoice_mkp': sale.invoice_mkp,
        })

    def sum_warehouse_product_quantity(self, sku, wh):
        warehouse_quantity = 0
        warehouse_id = self.env['stock.warehouse'].sudo().search([
            ('id' ,'=' , wh)
        ])
        quant_ids = self.env['stock.quant'].sudo().search([
            '|', ('product_id.default_code','=', sku),
            ('product_id.barcode','=', sku),
            ('location_id.usage','=','internal'),
            ('location_id','=', warehouse_id.lot_stock_id.id)])
        warehouses = {}
        for quant in quant_ids:
            if quant.location_id:
                if quant.location_id not in warehouses:
                    warehouses.update({quant.location_id:0})
                warehouses[quant.location_id] += quant.available_quantity

        if warehouses:
            for location in warehouses:
                warehouse_quantity = warehouses[location]
        return warehouse_quantity

    def check_product(self, rec, meta):
        order_line = rec['order_line']
        count_success_by_order_line = len(rec['order_line'])
        wh = rec['warehouse_id']
        for line in order_line:
            Product = self.env['product.product']
            product_id = Product.search([('default_code', '=', line['sku'])])
            sku = product_id.default_code
            warehouse_qty = self.sum_warehouse_product_quantity(sku,wh)
            if not product_id\
                or warehouse_qty < line['product_uom_qty']:
                count_success_by_order_line -= 1
                meta['notif_import_line'].append((0,0,{
                    'order': rec['farmaku_order_mkp'],
                    'sku': line['sku'],
                    'product_name': line['product_name'],
                    'status': '',
                    'reason': "SKU not Found in Database"\
                        if not product_id else "Product Out of Stock",
                }))

        if count_success_by_order_line < len(rec['order_line']):
            meta['count_success'] -= len(rec['order_line'])
            meta['count_fail'] += len(rec['order_line'])
            rec = {}
        return rec, meta

    def prepare_fields(self, res, model_name):
        Model = self.env[model_name]
        res_list = {}
        disc = 0.0
        for key in res:
            if key not in Model._fields:
                continue
            if isinstance(Model._fields[key], fields.One2many):
                res_replacement = [(5, 0, 0)]
                for res_line in res[key]:
                    if key =='order_line':
                        product_id = self.env['product.product'].search([('default_code', '=', res_line['sku'])])
                        res_line.update({'name': '[%s] %s' %(product_id.default_code, product_id.name)}),
                        res_line.update({'product_id': product_id.id}),
                    res_line = self.prepare_fields(res_line, Model._fields[key].comodel_name)
                    res_replacement.append((0, 0, res_line))
                res_list[key] = res_replacement
            elif isinstance(Model._fields[key], fields.Integer):
                if isinstance(res[key], tuple):
                    res_list[key] = res[key][0]
                elif isinstance(res[key], int):
                    res_list[key] = res[key]
            else:
                res_list[key] = res[key]

        return res_list

    def execute_process_by_status(self, rec, sale_id, type):
        if sale_id.state != 'cancel':
            if type == 'cancel':
                if sale_id.state in ('sale', 'done'):
                    pass
                else:
                    sale_id.action_confirm()
                    sale_id.write({
                        'date_order': rec['date_order']
                    })
                    # Create AWB
                    if sale_id.is_airwaybill_mkp == True:
                        stock_picking = self.prepare_fields(rec, 'stock.picking')
                        sale_id.picking_ids.write({
                            'airway_bill': stock_picking['airway_bill'],
                            'shipping_source': stock_picking['shipping_source'],
                        })
                    # Create Invoice
                    if not sale_id.invoice_ids:
                        self.act_create_invoice(sale_id)
                    else:
                        account_move = self.prepare_fields(rec, 'account.move')
                        sale_id.invoice_ids.write({
                            'farmaku_order_mkp': account_move['farmaku_order_mkp'],
                            'invoice_mkp': account_move['invoice_mkp'],
                        })
                sale_id.with_context(disable_cancel_warning=True).action_cancel()
            elif type == 'open':
                if sale_id.state in ('sale', 'done'):
                    pass
                else:
                    sale_id.action_confirm()
                    sale_id.write({
                        'date_order': rec['date_order']
                    })
                    # Create AWB
                    if sale_id.is_airwaybill_mkp == True:
                        stock_picking = self.prepare_fields(rec, 'stock.picking')
                        sale_id.picking_ids.write({
                            'airway_bill': stock_picking['airway_bill'],
                            'shipping_source': stock_picking['shipping_source'],
                        })
                # Create Invoice
                if not sale_id.invoice_ids:
                    self.act_create_invoice(sale_id)
                else:
                    account_move = self.prepare_fields(rec, 'account.move')
                    sale_id.invoice_ids.write({
                        'farmaku_order_mkp': account_move['farmaku_order_mkp'],
                        'invoice_mkp': account_move['invoice_mkp'],
                    })
            elif type == 'process':
                if sale_id.state in ('sale', 'done'):
                    pass
                else:
                    sale_id.action_confirm()
                    sale_id.write({
                        'date_order': rec['date_order']
                    })
                    # Create AWB
                    if sale_id.is_airwaybill_mkp == True:
                        stock_picking = self.prepare_fields(rec, 'stock.picking')
                        sale_id.picking_ids.write({
                            'airway_bill': stock_picking['airway_bill'],
                            'shipping_source': stock_picking['shipping_source'],
                        })
                    # Create Invoice
                    if not sale_id.invoice_ids:
                        self.act_create_invoice(sale_id)
                    else:
                        account_move = self.prepare_fields(rec, 'account.move')
                        sale_id.invoice_ids.write({
                            'farmaku_order_mkp': account_move['farmaku_order_mkp'],
                            'invoice_mkp': account_move['invoice_mkp'],
                        })
                pick_type_id = sale_id.warehouse_id.pick_type_id
                picking_id = sale_id.picking_ids.filtered(lambda x: x.picking_type_id == pick_type_id)
                if picking_id.state != 'done':
                    for line in picking_id.move_line_ids_without_package:
                        line['qty_done'] = line.product_uom_qty
                    picking_id.button_validate()
            elif type == 'done':
                if sale_id.state in ('sale', 'done'):
                    pass
                else:
                    sale_id.action_confirm()
                    sale_id.write({
                        'date_order': rec['date_order']
                    })
                    # Create AWB
                    if sale_id.is_airwaybill_mkp == True:
                        stock_picking = self.prepare_fields(rec, 'stock.picking')
                        sale_id.picking_ids.write({
                            'airway_bill': stock_picking['airway_bill'],
                            'shipping_source': stock_picking['shipping_source'],
                        })
                    # Create Invoice
                    if not sale_id.invoice_ids:
                        self.act_create_invoice(sale_id)
                    else:
                        account_move = self.prepare_fields(rec, 'account.move')
                        sale_id.invoice_ids.write({
                            'farmaku_order_mkp': account_move['farmaku_order_mkp'],
                            'invoice_mkp': account_move['invoice_mkp'],
                        })
                # sale_id.test_picking()
                out_type_id = sale_id.warehouse_id.out_type_id
                picking_out_id = sale_id.picking_ids.filtered(lambda x: x.picking_type_id == out_type_id)
                pick_type_id = sale_id.warehouse_id.pick_type_id
                picking_pick_id = sale_id.picking_ids.filtered(lambda x: x.picking_type_id == pick_type_id)
                if picking_pick_id.state == 'done':
                    pass
                else:
                    picking_pick_id.write({
                        'move_line_ids_without_package': [(1, move.id, {
                            'qty_done': move.product_uom_qty
                        })for move in picking_pick_id.move_line_ids_without_package]
                    })
                    picking_pick_id.button_validate()
                if picking_out_id.state != 'done':
                    picking_out_id.write({
                        'move_line_ids_without_package': [(1, move.id, {
                            'qty_done': move.product_uom_qty
                        })for move in picking_out_id.move_line_ids_without_package]
                    })
                    picking_out_id.button_validate()

    def check_status(self, status):
        type_status = False
        if status:
            Status = self.env['status.mkp']
            status_id = Status.search([]).filtered(lambda self: self.status.replace(' ', '').replace('.', '')\
                == ''.join(status.splitlines()).replace(' ', '').replace('.', ''))
            type_status = status_id.status_type if status_id else False
        return type_status


    def check_status_mkp(self, rec, meta):
        status_mkp = rec['order_status_mkp']
        type_status = self.check_status(status_mkp)
        count_order_line = len(rec['order_line'])
        if type_status == False:
            meta['notif_import_line'].append((0,0,{
                'order': rec['farmaku_order_mkp'],
                'sku': '',
                'product_name': '',
                'status': status_mkp,
                'reason': "Status not Found in Database",
            }))
            meta['count_fail'] += count_order_line
            rec = {}
        else:
            meta['count_success'] += count_order_line
        
        return rec, meta, type_status