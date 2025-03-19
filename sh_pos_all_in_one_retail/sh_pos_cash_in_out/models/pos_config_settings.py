# Copyright (C) Softhealer Technologies.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import pytz
from requests.sessions import session


class ShPosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def sh_write_close_balance(self, vals):
        total_amount = 0.00
        if vals:
            session_obj = ''
            for each_vals in vals:
                total_amount += float(each_vals.get('subtotal'))
                session_obj = self.env['pos.session'].browse(
                    each_vals.get('session_id'))
            for statement in session_obj.statement_ids:
                statement.write({'balance_end_real': total_amount})
            return True
        else:
            return False

    @api.model
    def sh_force_cash_control_line(self, vals):
        total_amount = 0.00
        if vals:
            session_obj = ''
            for each_vals in vals:
                total_amount += float(each_vals.get('subtotal'))
                session_obj = self.env['pos.session'].browse(
                    each_vals.get('session_id'))
            for statement in session_obj.statement_ids:
                statement.write({'balance_end_real': total_amount})
            session_obj.action_pos_session_closing_control()
            session_obj._validate_session()
            return True

    @api.model
    def sh_cash_control_line(self, vals):
        total_amount = 0.00
        if vals:
            session_obj = ''
            for each_vals in vals:
                total_amount += float(each_vals.get('subtotal'))
                session_obj = self.env['pos.session'].browse(
                    each_vals.get('session_id'))
            if session_obj.cash_control and abs(session_obj.cash_register_difference) > session_obj.config_id.amount_authorized_diff:
                # Only pos manager can close statements with cash_register_difference greater than amount_authorized_diff.
                if not session_obj.user_has_groups("point_of_sale.group_pos_manager"):
                    raise UserError(_(
                        "Your ending balance is too different from the theoretical cash closing (%.2f), "
                        "the maximum allowed is: %.2f. You can contact your manager to force it."
                    ) % (self.cash_register_difference, self.config_id.amount_authorized_diff))
                else:
                    return False
            else:
                session_obj.action_pos_session_closing_control()
                session_obj._validate_session()
                return True


class ShCashInOut(models.Model):
    _name = 'sh.cash.in.out'
    _description = 'Cah In Cash Out'

    sh_transaction_type = fields.Selection(
        [('cash_in', 'Cash In'), ('cash_out', 'Cash Out')], string="Transaction Type", required="1")
    sh_amount = fields.Float(string="Amount")
    sh_reason = fields.Char(string="Reason")
    sh_session = fields.Many2one('pos.session', string="Session")
    sh_date = fields.Datetime(
        string='Date', readonly=True, index=True, default=fields.Datetime.now)


class CashBoxOut(models.TransientModel):
    _inherit = 'cash.box.out'

    @api.model
    def sh_run(self, data):
        for each_data in data:
            cash_box_out_obj = ""
            if each_data.get('sh_transaction_type') and each_data.get('sh_transaction_type') == 'cash_in':
                cash_box_out_obj = self.create({'name': each_data.get(
                    'sh_reason'), 'amount': float(each_data.get('sh_amount'))})
            if each_data.get('sh_transaction_type') and each_data.get('sh_transaction_type') == 'cash_out':
                cash_box_out_obj = self.create({'name': each_data.get(
                    'sh_reason'), 'amount': -float(each_data.get('sh_amount'))})

            self.env['sh.cash.in.out'].create(each_data)
            bank_statements = [session.cash_register_id for session in self.env['pos.session'].browse(
                each_data.get('sh_session')) if session.cash_register_id]
            if not bank_statements:
                raise UserError(
                    _("There is no cash register for this PoS Session"))
            cash_box_out_obj._run(bank_statements)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_is_cash_in_out = fields.Boolean(string="Is Cash In Out From POS ?")
    sh_print_information = fields.Boolean(
        string="Print Information In Receipt ?")
    sh_signature_part_receipt = fields.Boolean(
        string="Is Signature Part In Receipt ?")
    sh_set_closing_at_close = fields.Boolean(
        string="Is Set Closing Balance During Close POS ?")
