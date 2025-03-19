import time
import base64
import logging

from odoo import fields, models, api, modules
from xlrd import open_workbook

_logger = logging.getLogger(__name__)


class MsMagicButton(models.TransientModel):
    _name = "ms.magic.button"
    _description = "Magic Button"

    action = fields.Selection([
        ('remove_missing_filestore', 'Remove Missing Filestore'),
        ('remove_missing_module', 'Remove Missing Module'),
        ('purchase_sale_price_revision', 'Revisi Harga PO dan SO'),
        ('patching_data_1', 'Patching Data 01-01-2025'),
    ], string="Action")
    file = fields.Binary(string='File')
    filename = fields.Char(string='Filename')

    def action_magic(self):
        if self.action == 'remove_missing_filestore':
            self.action_remove_missing_filestore()
        if self.action == 'remove_missing_module':
            self.action_remove_missing_module()
        if self.action == 'purchase_sale_price_revision':
            self.action_purchase_sale_price_revision()
        if self.action == 'patching_data_1':
            self.action_patching_data_1()

    def action_remove_missing_filestore(self):
        attachment_ids = self.env['ir.attachment'].search([
            ('store_fname', '!=', False),
            ('type', '=', 'binary'),
            ('is_valid', '=', False),
            ('id', '!=', 100),  # ada yg aneh, kalau gak ditambah ID dapatnya sedikit
        ], limit=100)
        attachment_total = len(attachment_ids)
        current_index = 1
        for attachment_id in attachment_ids:
            _logger.info("\n\n Proses attachment ke %d/%d", current_index, attachment_total)
            full_path = attachment_id._full_path(attachment_id.store_fname)
            r = ''
            bin_size = attachment_id._context.get('bin_size')
            try:
                if bin_size:
                    r = human_size(os.path.getsize(full_path))
                else:
                    r = base64.b64encode(open(full_path, 'rb').read())
                    attachment_id.is_valid = True
            except (IOError, OSError):
                _logger.info("\n\n Remove attachment %s", full_path)
            if not r:
                attachment_id.unlink()
            current_index += 1

    def action_remove_missing_module(self):
        module_ids = self.env['ir.module.module'].sudo().search([])
        attachment_total = len(module_ids)
        current_index = 1
        for module in module_ids:
            _logger.info("\n\n Proses module ke %d/%d", current_index, attachment_total)
            if not modules.get_module_path(module.name) and module.state != 'installed':
                model_constraint_id = self.env['ir.model.constraint'].search([('module', '=', module.id)])
                model_constraint_id.unlink()
                _logger.info("\n\n Remove module %s", module.name)
                module.unlink()
            current_index += 1

    def action_purchase_sale_price_revision(self):
        self = self.sudo()
        wb = open_workbook(file_contents=base64.decodebytes(self.file))
        sheet_number = 1
        for s in wb.sheets():
            if sheet_number == 1:
                for row in range(s.nrows):
                    row_value = []
                    for col in range(s.ncols):
                        value = s.cell(row, col).value
                        row_value.append(value)
                    try:
                        int(row_value[1])
                    except Exception:
                        continue
                    if not row:
                        continue
                    line_id = int(row_value[1])
                    price_unit = float(row_value[5])
                    line_id = self.env['purchase.order.line'].search([
                        ('id', '=', line_id)
                    ])
                    if not line_id:
                        continue
                    prev_price_unit = line_id.price_unit
                    line_id.write({
                        'price_unit': price_unit,
                    })
                    for move_id in line_id.move_ids:
                        for valuation_layer_id in move_id.stock_valuation_layer_ids:
                            unit_cost = line_id.product_uom._compute_price(price_unit, valuation_layer_id.uom_id)
                            valuation_layer_id.write({
                                'unit_cost': unit_cost,
                                'value': unit_cost * valuation_layer_id.quantity,
                            })
                            valuation_layer_id.account_move_id.button_draft()
                            for account_move_line_id in valuation_layer_id.account_move_id.line_ids:
                                if account_move_line_id.debit:
                                    account_move_line_id.with_context(check_move_validity=False).write({
                                        'debit': unit_cost * valuation_layer_id.quantity
                                    })
                                elif account_move_line_id.credit:
                                    account_move_line_id.with_context(check_move_validity=False).write({
                                        'credit': unit_cost * valuation_layer_id.quantity
                                    })
                            valuation_layer_id.account_move_id._post()
            elif sheet_number == 2:
                move_orig_ids = self.env['stock.move']
                for row in range(s.nrows):
                    row_value = []
                    for col in range(s.ncols):
                        value = s.cell(row, col).value
                        row_value.append(value)
                    try:
                        int(row_value[1])
                    except Exception:
                        continue
                    if not row:
                        continue
                    line_id = int(row_value[1])
                    price_unit = float(row_value[6])
                    line_id = self.env['sale.order.line'].search([
                        ('id', '=', line_id)
                    ])
                    if not line_id:
                        continue
                    prev_price_unit = line_id.price_unit
                    line_id.write({
                        'price_unit': price_unit,
                    })
                    for move_id in line_id.move_ids:
                        for valuation_layer_id in move_id.stock_valuation_layer_ids:
                            unit_cost = line_id.product_uom._compute_price(price_unit, valuation_layer_id.uom_id)
                            value = abs(unit_cost * valuation_layer_id.quantity)
                            valuation_layer_id.write({
                                'unit_cost': unit_cost,
                                'value': value,
                            })
                            valuation_layer_id.account_move_id.button_draft()
                            for account_move_line_id in valuation_layer_id.account_move_id.line_ids:
                                if account_move_line_id.debit:
                                    account_move_line_id.with_context(check_move_validity=False).write({
                                        'debit': value
                                    })
                                elif account_move_line_id.credit:
                                    account_move_line_id.with_context(check_move_validity=False).write({
                                        'credit': value
                                    })
                            valuation_layer_id.account_move_id._post()
                        move_orig_ids |= move_id.move_orig_ids
                    for move_id in move_orig_ids:
                        for valuation_layer_id in move_id.stock_valuation_layer_ids:
                            unit_cost = line_id.product_uom._compute_price(price_unit, valuation_layer_id.uom_id)
                            value = abs(unit_cost * valuation_layer_id.quantity)
                            print('\n value', value)
                            valuation_layer_id.write({
                                'unit_cost': unit_cost,
                                'value': value,
                            })
                            valuation_layer_id.account_move_id.button_draft()
                            for account_move_line_id in valuation_layer_id.account_move_id.line_ids:
                                if account_move_line_id.debit:
                                    account_move_line_id.with_context(check_move_validity=False).write({
                                        'debit': value
                                    })
                                elif account_move_line_id.credit:
                                    account_move_line_id.with_context(check_move_validity=False).write({
                                        'credit': value
                                    })
                            valuation_layer_id.account_move_id._post()
            sheet_number += 1

    def action_patching_data_1(self):
        query = ''
        self = self.sudo()
        sale_obj = self.env['sale.order']
        trx_datetime = '2024-12-31 17:00:00'
        not_found_ids = [0]
        sale_ids = sale_obj.search([
            ('date_order', '>=', trx_datetime),
            ('name', 'ilike', '2412'),
        ])
        picking_ids = sale_ids.mapped('picking_ids')
        invoice_ids = sale_ids.mapped('invoice_ids')
        sale_ids_str = str(tuple(sale_ids.ids + not_found_ids)).replace(',)', ')')
        picking_ids_str = str(tuple(picking_ids.ids + not_found_ids)).replace(',)', ')')
        invoice_ids_str = str(tuple(invoice_ids.ids + not_found_ids)).replace(',)', ')')
        _logger.info(f'sale from 24 to 25: {sale_ids_str}')
        _logger.info(f'picking from 24 to 25: {picking_ids_str}')
        _logger.info(f'invoice from 24 to 25: {invoice_ids_str}')
        query += f"""
            UPDATE 
                sale_order
            SET 
                name = REPLACE(name, '2412', '2501')
            WHERE
                id in {sale_ids_str};
            UPDATE 
                stock_picking
            SET 
                name = REPLACE(name, '2412', '2501')
            WHERE
                id in {picking_ids_str};
            UPDATE 
                account_move
            SET 
                name = REPLACE(name, '2412', '2501'),
                new_name = REPLACE(name, '2412', '2501'),
                payment_reference = REPLACE(name, '2412', '2501'),
                invoice_origin = REPLACE(invoice_origin, '2412', '2501')
            WHERE
                id in {invoice_ids_str};
        """
        sale_ids = sale_obj.search([
            ('date_order', '<', trx_datetime),
            ('name', 'ilike', '2501'),
        ])
        sale_line_ids = sale_ids.mapped('order_line')
        picking_ids = sale_ids.mapped('picking_ids')
        invoice_ids = sale_ids.mapped('invoice_ids')
        invoice_line_ids = invoice_ids.mapped('invoice_line_ids')
        sale_ids_str = str(tuple(sale_ids.ids + not_found_ids)).replace(',)', ')')
        sale_line_ids_str = str(tuple(sale_line_ids.ids + not_found_ids)).replace(',)', ')')
        picking_ids_str = str(tuple(picking_ids.ids + not_found_ids)).replace(',)', ')')
        invoice_ids_str = str(tuple(invoice_ids.ids + not_found_ids)).replace(',)', ')')
        invoice_line_ids_str = str(tuple(invoice_line_ids.ids + not_found_ids)).replace(',)', ')')
        query += f"""
            UPDATE 
                sale_order
            SET 
                name = REPLACE(name, '2501', '2412')
            WHERE
                id in {sale_ids_str};
            UPDATE 
                stock_picking
            SET 
                name = REPLACE(name, '2501', '2412')
            WHERE
                id in {picking_ids_str};
            UPDATE 
                account_move
            SET 
                name = REPLACE(name, '2501', '2412'),
                new_name = REPLACE(name, '2501', '2412'),
                payment_reference = REPLACE(name, '2501', '2412'),
                invoice_origin = REPLACE(invoice_origin, '2501', '2412')
            WHERE
                id in {invoice_ids_str};
        """
        _logger.info(f'sale from 25 to 24: {sale_ids_str}')
        _logger.info(f'picking from 25 to 24: {picking_ids_str}')
        _logger.info(f'invoice from 25 to 24: {invoice_ids_str}')
        query += f"""
            UPDATE 
                account_tax_sale_order_line_rel
            SET 
                account_tax_id = 1
            WHERE
                account_tax_id = 32
                AND sale_order_line_id in {sale_line_ids_str};
            UPDATE 
                account_move_line_account_tax_rel
            SET 
                account_tax_id = 1
            WHERE
                account_tax_id = 32
                AND account_move_line_id in {invoice_line_ids_str};
            UPDATE 
                account_tax_sale_order_line_rel
            SET 
                account_tax_id = 7
            WHERE
                account_tax_id = 40
                AND sale_order_line_id in {sale_line_ids_str};
            UPDATE 
                account_move_line_account_tax_rel
            SET 
                account_tax_id = 7
            WHERE
                account_tax_id = 40
                AND account_move_line_id in {invoice_line_ids_str};
        """
        query += f"""
            UPDATE 
                account_move
            SET 
                name = 'INVS24120001790',
                new_name = 'INVS24120001790',
                payment_reference = 'INVS24120001790'
            WHERE
                name = 'INVS25010001790';
            UPDATE 
                account_move
            SET 
                name = 'INVS24120001694',
                new_name = 'INVS24120001694',
                payment_reference = 'INVS24120001694'
            WHERE
                name = 'INVS25010001694';
            UPDATE 
                purchase_order
            SET 
                name = 'PN2501000001'
            WHERE
                name = 'PN2412000001';
            UPDATE 
                purchase_order
            SET 
                name = 'PS2501000001'
            WHERE
                name = 'PS2412000001';
        """
        # source document sebelumnya kelewat
        query += f"""
            UPDATE 
                account_move
            SET 
                invoice_origin = REPLACE(invoice_origin, '2412', '2501')
            WHERE
                name ILIKE '%2501%' AND invoice_origin NOT ILIKE '%2501%';
            UPDATE 
                account_move
            SET 
                invoice_origin = REPLACE(invoice_origin, '2501', '2412')
            WHERE
                name ILIKE '%2412%' AND invoice_origin NOT ILIKE '%2412%';
        """
        if query:
            self.env.cr.execute(query=query)
