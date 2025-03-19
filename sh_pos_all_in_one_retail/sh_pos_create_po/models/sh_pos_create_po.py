# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import fields, models, api
from odoo.exceptions import UserError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_dispaly_purchase_btn = fields.Boolean("Enable Purchase Order")
    select_purchase_state = fields.Selection(
        [('rfq', 'RFQ'), ('purchase_order', 'Purchase Order')], string="Select Purchase Order State", default="rfq")

    @api.model
    def sh_create_purchase_line(self,line,order_id):
        
        if len(line) > 0:
            for each_line in line:
                each_line['order_id'] = order_id
                if each_line.get('taxes_id'):
                    taxes = []
                    for each_tax in each_line.get('taxes_id'):
                        tax_obj = self.env['account.tax'].search([('id','=',each_tax)])
                        if tax_obj.type_tax_use == 'purchase':
                            self.env['purchase.order.line'].create(each_line)
                        else:
                            purchase_tax_obj = self.env['account.tax'].search(['&',('type_tax_use','=','purchase'),('name','ilike',tax_obj.name)],limit=1)
                            if purchase_tax_obj:
                                taxes.append(purchase_tax_obj.id)
                    each_line['taxes_id'] = taxes
                    self.env['purchase.order.line'].create(each_line)
                else:
                    self.env['purchase.order.line'].create(each_line)
                    
    @api.onchange('sh_dispaly_purchase_btn')
    def _onchange_sh_display_purchase_btn(self):
        stock_app = self.env['ir.module.module'].sudo().search(
            [('name', '=', 'purchase')], limit=1)
        if self.sh_dispaly_purchase_btn:
            if stock_app.state != 'installed':
                self.sh_dispaly_purchase_btn = False
                raise UserError('Purchase Module not installed ! Please install Purchase module first.')    

# class PosOrder(models.Model):
#     _inherit = 'purchase.order'

#     def pos_create_po(self, vals):
#         for val in vals:
#             if val:
#                 rec = self.create({'partner_id': val.get('partner_id')})
#                 for line in val.get('order_lines'):
#                     if line:
#                         line.update({'order_id': rec.id})
#                         self.env['purchase.order.line'].create(line)
#                 if val.get('state') and val.get('state') == 'purchase_order':
#                     rec.button_confirm()
#         return True
