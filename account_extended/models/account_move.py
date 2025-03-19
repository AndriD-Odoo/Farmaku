from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date
from datetime import datetime


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_report_base_filename(self):
        res = super(AccountMove, self)._get_report_base_filename()
        if self.env.context.get('commercial_invoice'):
            res = f'Commercial Invoice {self.name}'
            if self.move_type in ['in_refund', 'out_refund']:
                res = f'Credit Note {self.name}'
            elif self.move_type not in ['in_invoice', 'out_invoice']:
                res = f'Journal Entry {self.name}'
        return res

    receiver_pic_id = fields.Many2one(
        comodel_name='res.partner',
        string='Receiver PIC',
        required=False)
    sender_pic_id = fields.Many2one(
        comodel_name='res.partner',
        string='Sender PIC',
        required=False)
    partner_contact_ids = fields.One2many(
        comodel_name='res.partner',
        related='partner_id.child_ids',
        string='Partner Contacts')
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=False)
    warehouse_contact_ids = fields.One2many(
        comodel_name='res.partner',
        related='warehouse_id.partner_id.child_ids',
        string='Warehouse Contacts')

    @api.onchange('warehouse_id')
    def onchange_warehouse(self):
        self.sender_pic_id = False

    def get_partner_contact(self):
        contact = ''
        if self.partner_id.child_ids:
            contact = self.partner_id.child_ids[0].name
        return contact

    def get_order_date(self):
        order_date = ''
        sale_ids = self.invoice_line_ids.mapped('sale_line_ids.order_id')
        if sale_ids:
            order_date = sale_ids[0].date_order.date()
        if not order_date:
            sale_id = self.env['sale.order'].search([
                ('name', '=', self.invoice_origin)
            ], limit=1)
            if sale_id:
                order_date = sale_id.date_order.date()
        if not order_date and self.invoice_date:
            order_date = self.invoice_date.date()
        if order_date:
            order_date = order_date.strftime('%d %B %Y')
        return order_date

    def reformat_commercial_date(self, date):
        converted_date = ''
        if date:
            if isinstance(date, str):
                date = datetime.strptime(date, '%Y-%m-%d')
            converted_date = date.strftime('%d %B %Y')
        return converted_date

    def get_discount_amount(self):
        discount_amount = 0
        line_discount_ids = self.invoice_line_ids.filtered(lambda l: l.discount)
        for line in line_discount_ids:
            discount_amount += (line.quantity * line.price_unit) * line.discount / 100
        return discount_amount
