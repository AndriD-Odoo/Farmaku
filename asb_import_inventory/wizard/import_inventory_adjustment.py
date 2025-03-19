from odoo import api, fields, models, _, tools, SUPERUSER_ID
import os
import csv
from odoo.modules import get_module_path
from odoo.exceptions import UserError
import copy
from io import StringIO
import base64
import odoo.tools
from datetime import datetime, timedelta

import logging
_logger = logging.getLogger(__name__)


class ImportInventoryAdjustment(models.TransientModel):
    _name = 'import.inventory.adjustment'
    _description = 'Import Inventory Adjustment'

    name = fields.Char(string='Import Inventory')

    def confirm_button(self):
        cr = self.env.cr
        dir_path = os.path.dirname(os.path.realpath(__file__))

        with open(dir_path + '/inventory.asb.csv', 'rt') as csvfile:
            partner = []
            company = 1
            prefill = "counted"
            state = "draft"
            date = datetime.today()
            inventory_values = []
            stock = self.env['stock.inventory'].search([])
            for row in csv.DictReader(csvfile, delimiter=',', quotechar='"'):
                if row['Inventory Reference'] != '':
                    inventory_values.append(cr.mogrify('( %s, %s, %s, %s, %s)', (
                        date,
                        state,
                        company,
                        prefill,
                        row['Inventory Reference'])).decode())
            if inventory_values:
                cr.execute("""
                WITH insert_data AS (
                    INSERT INTO stock_inventory (date, state, company_id, prefill_counted_quantity, name) VALUES %s RETURNING id)
                INSERT INTO ir_model_data (module, name, model, res_id) SELECT 'asb_import_inventory', CONCAT('asb_import_inventory_asb',id::TEXT), 'product_template', id FROM insert_data
                """ % ','.join(inventory_values))

        with open(dir_path + '/inventory.asb.csv', 'rt') as csvfile:
            company = 1
            uom = 1
            procure = "make_to_stock"
            date = datetime.today()
            inventory_line_values = []
            stock_move_line_values = []
            stock = self.env['stock.inventory'].search([])
            last = max(stock)
            for row2 in csv.DictReader(csvfile, delimiter=',', quotechar='"'):
                if int(row2['Inventories / Counted Quantity']) > 0:
                    product = self.env['product.product'].search([('barcode', '=', row2['Inventories/Product'])])
                    location = self.env['stock.location'].search([('complete_name', '=', row2['Inventories/Location'])])
                    if product:
                        inventory_line_values.append(cr.mogrify('(%s, %s, %s, %s, %s, %s, %s, %s, %s)', (
                        date,
                        product.id,
                        product.uom_id.id,
                        product.categ_id.id,
                        company,
                        last.id,
                        row2['Inventories / Counted Quantity'],
                        0,
                        location.id)).decode())
            if inventory_line_values:
                cr.execute("""
                WITH insert_data AS (
                    INSERT INTO stock_inventory_line (inventory_date, product_id, product_uom_id, categ_id, company_id, inventory_id, product_qty, theoretical_qty, location_id) VALUES %s RETURNING id)
                INSERT INTO ir_model_data (module, name, model, res_id) SELECT 'asb_import_inventory', CONCAT('asb_import_inventory_line_asb',id::TEXT), 'product_template', id FROM insert_data
                """ % ','.join(inventory_line_values))

        with open(dir_path + '/inventory.mkp.csv', 'rt') as csvfile:
            partner = []
            company = 1
            prefill = "counted"
            state = "draft"
            date = datetime.today()
            inventory_values = []
            stock = self.env['stock.inventory'].search([])
            for row3 in csv.DictReader(csvfile, delimiter=',', quotechar='"'):
                if row3['Inventory Reference'] != '':
                    inventory_values.append(cr.mogrify('( %s, %s, %s, %s, %s)', (
                        date,
                        state,
                        company,
                        prefill,
                        row3['Inventory Reference'])).decode())
            if inventory_values:
                cr.execute("""
                WITH insert_data AS (
                    INSERT INTO stock_inventory (date, state, company_id, prefill_counted_quantity, name) VALUES %s RETURNING id)
                INSERT INTO ir_model_data (module, name, model, res_id) SELECT 'asb_import_inventory', CONCAT('asb_import_inventory_mkp',id::TEXT), 'product_template', id FROM insert_data
                """ % ','.join(inventory_values))

        with open(dir_path + '/inventory.mkp.csv', 'rt') as csvfile:
            company = 1
            uom = 1
            procure = "make_to_stock"
            date = datetime.today()
            inventory_line_values = []
            stock_move_line_values = []
            stock = self.env['stock.inventory'].search([])
            last = max(stock)
            for row4 in csv.DictReader(csvfile, delimiter=',', quotechar='"'):
                if int(row4['Inventories / Counted Quantity']) > 0:
                    product = self.env['product.product'].search([('barcode', '=', row4['Inventories/Product'])])
                    location = self.env['stock.location'].search([('complete_name', '=', row4['Inventories/Location'])])
                    if product:
                        inventory_line_values.append(cr.mogrify('(%s, %s, %s, %s, %s, %s, %s, %s, %s)', (
                        date,
                        product.id,
                        product.uom_id.id,
                        product.categ_id.id,
                        company,
                        last.id,
                        row4['Inventories / Counted Quantity'],
                        0,
                        location.id)).decode())
            if inventory_line_values:
                cr.execute("""
                WITH insert_data AS (
                    INSERT INTO stock_inventory_line (inventory_date, product_id, product_uom_id, categ_id, company_id, inventory_id, product_qty, theoretical_qty, location_id) VALUES %s RETURNING id)
                INSERT INTO ir_model_data (module, name, model, res_id) SELECT 'asb_import_inventory', CONCAT('asb_import_inventory_line_mkp',id::TEXT), 'product_template', id FROM insert_data
                """ % ','.join(inventory_line_values))

        with open(dir_path + '/inventory.web.csv', 'rt') as csvfile:
            partner = []
            company = 1
            prefill = "counted"
            state = "draft"
            date = datetime.today()
            inventory_values = []
            stock = self.env['stock.inventory'].search([])
            for row5 in csv.DictReader(csvfile, delimiter=',', quotechar='"'):
                if row5['Inventory Reference'] != '':
                    inventory_values.append(cr.mogrify('( %s, %s, %s, %s, %s)', (
                        date,
                        state,
                        company,
                        prefill,
                        row5['Inventory Reference'])).decode())
            if inventory_values:
                cr.execute("""
                WITH insert_data AS (
                    INSERT INTO stock_inventory (date, state, company_id, prefill_counted_quantity, name) VALUES %s RETURNING id)
                INSERT INTO ir_model_data (module, name, model, res_id) SELECT 'asb_import_inventory', CONCAT('asb_import_inventory_web',id::TEXT), 'product_template', id FROM insert_data
                """ % ','.join(inventory_values))

        with open(dir_path + '/inventory.web.csv', 'rt') as csvfile:
            company = 1
            uom = 1
            procure = "make_to_stock"
            date = datetime.today()
            inventory_line_values = []
            stock_move_line_values = []
            stock = self.env['stock.inventory'].search([])
            last = max(stock)
            for row6 in csv.DictReader(csvfile, delimiter=',', quotechar='"'):
                if int(row6['Inventories / Counted Quantity']) > 0:
                    product = self.env['product.product'].search([('barcode', '=', row6['Inventories/Product'])])
                    location = self.env['stock.location'].search([('complete_name', '=', row6['Inventories/Location'])])
                    if product:
                        inventory_line_values.append(cr.mogrify('(%s, %s, %s, %s, %s, %s, %s, %s, %s)', (
                        date,
                        product.id,
                        product.uom_id.id,
                        product.categ_id.id,
                        company,
                        last.id,
                        row6['Inventories / Counted Quantity'],
                        0,
                        location.id)).decode())
            if inventory_line_values:
                cr.execute("""
                WITH insert_data AS (
                    INSERT INTO stock_inventory_line (inventory_date, product_id, product_uom_id, categ_id, company_id, inventory_id, product_qty, theoretical_qty, location_id) VALUES %s RETURNING id)
                INSERT INTO ir_model_data (module, name, model, res_id) SELECT 'asb_import_inventory', CONCAT('asb_import_inventory_line_web',id::TEXT), 'product_template', id FROM insert_data
                """ % ','.join(inventory_line_values))

        with open(dir_path + '/inventory.tmg.csv', 'rt') as csvfile:
            partner = []
            company = 1
            prefill = "counted"
            state = "draft"
            date = datetime.today()
            inventory_values = []
            stock = self.env['stock.inventory'].search([])
            for row7 in csv.DictReader(csvfile, delimiter=',', quotechar='"'):
                if row7['Inventory Reference'] != '':
                    inventory_values.append(cr.mogrify('( %s, %s, %s, %s, %s)', (
                        date,
                        state,
                        company,
                        prefill,
                        row7['Inventory Reference'])).decode())
            if inventory_values:
                cr.execute("""
                WITH insert_data AS (
                    INSERT INTO stock_inventory (date, state, company_id, prefill_counted_quantity, name) VALUES %s RETURNING id)
                INSERT INTO ir_model_data (module, name, model, res_id) SELECT 'asb_import_inventory', CONCAT('asb_import_inventory_tmg',id::TEXT), 'product_template', id FROM insert_data
                """ % ','.join(inventory_values))

        with open(dir_path + '/inventory.tmg.csv', 'rt') as csvfile:
            company = 1
            uom = 1
            procure = "make_to_stock"
            date = datetime.today()
            inventory_line_values = []
            stock_move_line_values = []
            stock = self.env['stock.inventory'].search([])
            last = max(stock)
            for row8 in csv.DictReader(csvfile, delimiter=',', quotechar='"'):
                if int(row8['Inventories / Counted Quantity']) > 0 :
                    template = self.env['product.template'].search([('import_code', '=', row8['Inventories/Product'])])
                    product = self.env['product.product'].search([('product_tmpl_id', '=', template.id)])
                    location = self.env['stock.location'].search([('complete_name', '=', row8['Inventories/Location'])])
                    if product:
                        inventory_line_values.append(cr.mogrify('(%s, %s, %s, %s, %s, %s, %s, %s, %s)', (
                        date,
                        product.id,
                        product.uom_id.id,
                        product.categ_id.id,
                        company,
                        last.id,
                        row8['Inventories / Counted Quantity'],
                        0,
                        location.id)).decode())
            if inventory_line_values:
                cr.execute("""
                WITH insert_data AS (
                    INSERT INTO stock_inventory_line (inventory_date, product_id, product_uom_id, categ_id, company_id, inventory_id, product_qty, theoretical_qty, location_id) VALUES %s RETURNING id)
                INSERT INTO ir_model_data (module, name, model, res_id) SELECT 'asb_import_inventory', CONCAT('asb_import_inventory_line_tmg',id::TEXT), 'product_template', id FROM insert_data
                """ % ','.join(inventory_line_values))