from odoo import api, fields, models, _, tools, SUPERUSER_ID
import os
import csv
from odoo.modules import get_module_path
from datetime import datetime, timedelta

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'Product Template'
    
    import_code = fields.Char(string='Product ID Farmaku')

class ImportProducts(models.Model):
    _name = 'import.product'
    _description = 'Import Product'
    
    name = fields.Char(string='Import Product')

    def confirm_button(self):
        cr = self.env.cr
        dir_path = os.path.dirname(os.path.realpath(__file__))

        with open(dir_path + '/product.test.csv', 'rt') as csvfile:
            tracking = 'none'
            sequence = '1'
            active = 'True'
            product_type = []
            product_values = []
            product_product_values = []
            ir_property_value = []
            ir_property_inventory = []
            product = self.env['product.template'].search([])
            product_size = len(product)
            for row in csv.DictReader(csvfile, delimiter=',', quotechar='"'):
                match = product.filtered(lambda rec: row['name'] == rec.name)
                if not match:
                    category = self.env['product.category'].search([('complete_name', '=', row['categ_id'])])
                    uom_id = self.env['uom.uom'].search([('name', '=', row['uom_id'])])
                    uom_po_id = self.env['uom.uom'].search([('name', '=', row['uom_id'])])
                    if row['type'] == 'Storable Product':
                        product_type = 'product'
                    elif row['type'] == 'Consumable Product':
                        product_type = 'consumable'
                    elif row['type'] == 'Service':
                        product_type = 'service'

                    if row['purchase_method'] == 'On received quantities':
                        purchase_method = 'purchase'
                    elif row['purchase_method'] == 'On received quantities':
                        purchase_method = 'receive'

                    if row['invoice_policy'] == 'Ordered quantities':
                        invoice_policy = 'order'
                    elif row['invoice_policy'] == 'Delivered quantities':
                        invoice_policy = 'delivery'

                    product_values.append(cr.mogrify('(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (
                        product_type,
                        row['id'],
                        row['default_code'],
                        category.id,
                        uom_id.id,
                        uom_po_id.id,
                        sequence,
                        active,
                        tracking,
                        purchase_method, 
                        invoice_policy,
                        "True",
                        "True",
                        "True",
                        "no-message",
                        "no-message",
                        row['lst_price'],
                        row['name'])).decode())
            if product_values:
                cr.execute("""
                WITH insert_data AS (
                    INSERT INTO product_template (type, import_code, default_code, categ_id, uom_po_id, uom_id, sequence, active, tracking, purchase_method, invoice_policy, sale_ok, purchase_ok, available_in_pos, sale_line_warn, purchase_line_warn, list_price, name) VALUES %s RETURNING id)
                INSERT INTO ir_model_data (module, name, model, res_id) SELECT 'asb_import_product', CONCAT('product_template',id::TEXT), 'product_template', id FROM insert_data
                """ % ','.join(product_values))

        with open(dir_path + '/product.test.csv', 'rt') as csvfile:
            product_product = self.env['product.product'].search([])
            for row2 in csv.DictReader(csvfile, delimiter=',', quotechar='"'):
                match = product_product.filtered(lambda rec: row2['barcode'] == rec.barcode)
                if not match:
                    product2 = self.env['product.template'].search([('import_code','=',row2['id'])])
                    product_product_values.append(cr.mogrify('(%s,%s,%s,%s)', (
                        product2[0].id,
                        row2['barcode'],
                        row2['default_code'], 
                        active)).decode())
            if product_product_values:
                cr.execute("""
                WITH insert_data AS (
                    INSERT INTO product_product (product_tmpl_id, barcode, default_code, active) VALUES %s RETURNING id)
                INSERT INTO ir_model_data (module, name, model, res_id) SELECT 'asb_import_product', CONCAT('product_product',id::TEXT), 'product_product', id FROM insert_data
                """ % ','.join(product_product_values))
        
        with open(dir_path + '/product.test.csv', 'rt') as csvfile:
            property_data = self.env['ir.property'].search([])
            standard_price = self.env['ir.model.fields'].search([('model','=','product.product'),('name','=','standard_price')])
            property_stock_inventory = self.env['ir.model.fields'].search([('model','=','product.template'),('name','=','property_stock_inventory')])
            company = '1'
            for row3 in csv.DictReader(csvfile, delimiter=',', quotechar='"'):
                product = self.env['product.template'].search([('import_code','=',row3['id'])])
                product_product = self.env['product.product'].search([('product_tmpl_id','=',product.id)])
                stock_location = self.env['stock.location'].search([('complete_name','=',row3['property_stock_inventory'])])

                fields_type = 'float'
                fields_type_inventory = 'many2one'
                
                res_id = str('product.product,%s' % product_product.id)
                res_id_inventory = str('product.template,%s' % product.id)
                value_reference = str('stock.location,%s' % stock_location[0].id)

                match = property_data.filtered(lambda rec: 'standard_price' == rec.fields_id.name and res_id == rec.res_id )
                match_inventory = property_data.filtered(lambda rec: 'property_stock_inventory' == rec.fields_id.name and res_id_inventory == rec.res_id )

                if not match:
                    ir_property_value.append(cr.mogrify('(%s,%s,%s,%s,%s,%s)', (
                        standard_price.name,
                        company,
                        res_id,
                        fields_type,
                        standard_price.id,
                        row3['standard_price'])).decode())
                
                if not match_inventory:
                    ir_property_inventory.append(cr.mogrify('(%s,%s,%s,%s,%s,%s)', (
                        property_stock_inventory.name,
                        res_id_inventory,
                        company,
                        property_stock_inventory.id,
                        value_reference,
                        fields_type_inventory)).decode())
                        
            if ir_property_value:
                cr.execute("""
                    INSERT INTO ir_property (name, company_id, res_id, type, fields_id, value_float) VALUES %s
                """ % ','.join(ir_property_value))
            
            if ir_property_inventory:
                cr.execute("""
                    INSERT INTO ir_property (name, res_id, company_id, fields_id, value_reference, type) VALUES %s
                """ % ','.join(ir_property_inventory))