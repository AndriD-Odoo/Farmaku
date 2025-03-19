from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
import base64
from xlrd import open_workbook
import ast

class ImportFailedOrderWizard(models.TransientModel):
    _name = "import.failed.order.wizard"
    _description = "Import Failed Order"

    name = fields.Char()
    file = fields.Binary(required=True)
    is_validate_picking = fields.Boolean('Validate Picking', default=True)

    def button_import(self):
        wb = open_workbook(file_contents=base64.decodebytes(self.file))
        for s in wb.sheets():
            for row in range(s.nrows):
                row_value = []
                for col in range(s.ncols):
                    value = (s.cell(row, col).value)
                    row_value.append(value)
                try :
                    int(row_value[0])
                except :
                    continue
                if not row :
                    continue
                data = row_value[1].replace('null','""').replace('false','""').replace('true','1')
                data = ast.literal_eval(data)
                data.update({
                    'bypass_sync': True,
                })
                result = self.env['sale.order'].with_context({'is_validate_picking':self.is_validate_picking}).api_post_sale_order(body={'data':data})
                if result['code'] == 400 :
                    raise ValidationError(_(result['message']))
                sale_order_id = self.env['sale.order'].sudo().search([('farmaku_order_id', '=', result['order_id'])], order='id desc', limit=1)
                for line in sale_order_id.order_line:
                    if line.product_id.purchase_method != 'purchase':
                        line.product_id.purchase_method = 'purchase'
                if sale_order_id.state == 'draft':
                    sale_order_id.action_confirm()
                    if sale_order_id.state == 'sale':
                        invoice = sale_order_id.env["sale.advance.payment.inv"].create({})
                        invoice.with_context(active_ids=sale_order_id.ids).create_invoices()
                        for invoice in sale_order_id.invoice_ids:
                            invoice.with_company(invoice.company_id).action_post()
                            if invoice.state == 'posted':
                                payment = invoice.env['account.payment.register'].with_context \
                                    (active_model=invoice._name, active_ids=invoice.ids,
                                     dont_redirect_to_payments=True) \
                                    .create({}).action_create_payments()
                if self.is_validate_picking :
                    pick_picking_ids = sale_order_id.picking_ids.filtered(lambda p: p.location_dest_id.usage != 'customer')
                    out_picking_ids = sale_order_id.picking_ids.filtered(lambda p: p.location_dest_id.usage == 'customer')
                    is_need_to_enter_airway_bill = False
                    for picking in pick_picking_ids :
                        if picking.state != 'assigned':
                            continue
                        for line in picking.move_line_ids :
                            line.write({'qty_done':line.product_uom_qty})
                        if sale_order_id.is_need_to_enter_airway_bill :
                            sale_order_id.write({'is_need_to_enter_airway_bill':False})
                            is_need_to_enter_airway_bill = True
                        picking.button_validate()
                        if is_need_to_enter_airway_bill :
                            sale_order_id.write({'is_need_to_enter_airway_bill': True})
                    for picking in out_picking_ids :
                        if picking.state != 'assigned':
                            continue
                        for line in picking.move_line_ids :
                            line.write({'qty_done':line.product_uom_qty})
                        if sale_order_id.is_need_to_enter_airway_bill:
                            sale_order_id.write({'is_need_to_enter_airway_bill': False})
                            is_need_to_enter_airway_bill = True
                        picking.button_validate()
                        if is_need_to_enter_airway_bill:
                            sale_order_id.write({'is_need_to_enter_airway_bill': True})
