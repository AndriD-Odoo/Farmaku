# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_display_sale_btn = fields.Boolean(string="Enable sale order")
    select_order_state = fields.Selection([('quotation', 'Quotation'), ('confirm', 'Sale Order')], string="Select Order State", default="quotation")

    @api.onchange('sh_display_sale_btn')   
    def _onchange_mobile(self): 
        stock_app = self.env['ir.module.module'].sudo().search([('name','=','sale_management')],limit=1)
        if self.sh_display_sale_btn:
            if stock_app.state != 'installed':
                raise UserError(_("Sale Management Module not installed ! Please install Sale module first."))
    
    def pos_create_so(self, vals):
        order_ids = []
        for val in vals:
            if val:
                rec = self.env['sale.order'].create({'partner_id':val.get('partner_id'),'payment_term_id': val.get('payment_term_id')})
                for line in val.get('order_lines'):
                    if line:
                        line.update({'order_id': rec.id})
                        self.env['sale.order.line'].create(line)
                if val.get('state') and val.get('state') == 'confirm':
                    rec.action_confirm()
            order_ids.append({'id':rec.id, 'name': rec.name})
        return order_ids
           

# class SaleOrderinherit(models.Model):
#     _inherit = 'sale.order'

#     def pos_create_so(self, vals):
#         order_ids = []
#         for val in vals:
#             if val:
#                 rec = self.create({'partner_id':val.get('partner_id'),'payment_term_id': val.get('payment_term_id')})
#                 for line in val.get('order_lines'):
#                     if line:
#                         line.update({'order_id': rec.id})
#                         self.env['sale.order.line'].create(line)
#                 if val.get('state') and val.get('state') == 'confirm':
#                     rec.action_confirm()
#             order_ids.append({'id':rec.id, 'name': rec.name})
#         return order_ids
