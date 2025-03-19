# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

# Settlement Batch Model
class FarmakuSettlementBatch(models.Model):
    _name = 'farmaku.settlement.batch'
    _description = 'Settlement Batch'

    # Fields for the settlement batch
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    name = fields.Char(string='Name', required=True, default='/')
    sales_team = fields.Many2one('crm.team', string='Sales Team', required=True)

    # Define the one-to-many relationship with settlement lines
    settlement_line_ids = fields.One2many('farmaku.settlement.line', 'settlement_batch_id', string='Settlement Lines')

    # Add computed fields for total amounts
    total_net_amount = fields.Monetary(string='Total Net Amount', compute='_compute_amount', store=True)
    total_gross_amount = fields.Monetary(string='Total Gross Amount', compute='_compute_amount', store=True)
    total_subsidy_amount = fields.Monetary(string='Total Subsidy Amount', compute='_compute_amount', store=True)
    total_shipping_cost = fields.Monetary(string='Total Shipping Cost', compute='_compute_amount', store=True)
    total_voucher_amount = fields.Monetary(string='Total Voucher Amount', compute='_compute_amount', store=True)
    total_commission = fields.Monetary(string='Total Commission', compute='_compute_amount', store=True)
    total_service_fee = fields.Monetary(string='Total Service Fee', compute='_compute_amount', store=True)

    # Add a currency field to store the batch's currency
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    @api.depends('settlement_line_ids', 'settlement_line_ids.net_amount', 'settlement_line_ids.gross_amount', 'settlement_line_ids.subsidy_amount', 'settlement_line_ids.shipping_cost', 'settlement_line_ids.voucher_amount', 'settlement_line_ids.commission', 'settlement_line_ids.service_fee')
    def _compute_amount(self):
        for batch in self:
            total_net_amount = sum(batch.settlement_line_ids.mapped('net_amount'))
            total_gross_amount = sum(batch.settlement_line_ids.mapped('gross_amount'))
            total_subsidy_amount = sum(batch.settlement_line_ids.mapped('subsidy_amount'))
            total_shipping_cost = sum(batch.settlement_line_ids.mapped('shipping_cost'))
            total_voucher_amount = sum(batch.settlement_line_ids.mapped('voucher_amount'))
            total_commission = sum(batch.settlement_line_ids.mapped('commission'))
            total_service_fee = sum(batch.settlement_line_ids.mapped('service_fee'))

            batch.total_net_amount = total_net_amount
            batch.total_gross_amount = total_gross_amount
            batch.total_subsidy_amount = total_subsidy_amount
            batch.total_shipping_cost = total_shipping_cost
            batch.total_voucher_amount = total_voucher_amount
            batch.total_commission = total_commission
            batch.total_service_fee = total_service_fee

    # Existing method for generating invoice recap
    def action_generate_invoice_recap(self):
        try:
            self._validate_settlement_batch()
        except ValidationError as validation_error:
            return self._generate_error_response(validation_error.name)

        config_settings = self.env['res.config.settings'].sudo().get_values()
        missing_parameters = self._check_parameters(config_settings)
        if missing_parameters:
            error_message = "The following parameters are missing or empty:\n"
            error_message += "\n".join(missing_parameters)
            return self._generate_error_response(error_message)

        try:
            self._create_invoice_recap(config_settings)
        except Exception as create_error:
            return self._generate_error_response(str(create_error))

        success_message = "Invoice Recap Created successfully."
        return self._generate_success_response(success_message)

    def _validate_settlement_batch(self):
        for batch in self:
            errors = []

            if not all([batch.start_date, batch.end_date, batch.name, batch.sales_team, batch.currency_id]):
                errors.append("Required fields cannot be empty.")

            # Additional validation logic as needed

            if errors:
                error_message = '\n'.join(errors)
                raise ValidationError(error_message)

    def _check_parameters(self, config_settings):
        missing_parameters = []

        parameters = [
            'settlement_batch_product_id',
            'credit_account_gross_amount_id',
            'subsidy_credit_account_id',
            'debit_account_shipping_id',
            'debit_account_voucher_id',
            'debit_account_commission_id',
            'debit_account_service_fee_id',
            'debit_account_net_amount_id',
        ]

        for parameter in parameters:
            if not config_settings.get(parameter):
                missing_parameters.append(parameter)

        return missing_parameters  # Return the list of missing parameter names

    def _create_invoice_recap(self, config_settings):
        partner_id = self.sales_team.partner_id.id
        settlement_batch_product_id = self.env['product.product'].browse(config_settings.get('settlement_batch_product_id'))
        total_net_amount = self.total_net_amount
        current_user = self.env.uid

        # Find the default customer invoices journal
        journal_id = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)

        if not journal_id:
            raise Exception("No default customer invoices journal found.")

        # Create the invoice without lines first
        invoice_data = {
            'partner_id': partner_id,
            'invoice_date': fields.Date.today(),
            'journal_id': journal_id.id,
            'invoice_line_ids': [(0, 0, self._prepare_invoice_line_data(settlement_batch_product_id, journal_id, config_settings))],
            'state': 'draft',
            'move_type': 'out_invoice',
            'invoice_user_id': current_user,
            'currency_id': self.env.user.company_id.currency_id.id,
        }

        invoice = self.env['account.move'].create(invoice_data)

        # Create multiple account.move.line records
        move_lines = self._prepare_account_move_lines(config_settings)

        # Link the created account.move.line records to the invoice
        invoice.write({'line_ids': move_lines})

    def _prepare_account_move_lines(self, config_settings):
        move_lines = []

        total_gross_amount = self.total_gross_amount
        total_subsidy_amount = self.total_subsidy_amount
        total_shipping_cost = self.total_shipping_cost
        total_voucher_amount = self.total_voucher_amount
        total_commission = self.total_commission
        total_service_fee = self.total_service_fee
        total_net_amount = self.total_net_amount

        move_lines.append((0, 0, self._create_account_move_line("Total Gross Amount", 0.0, config_settings.get('total_gross_amount'), config_settings.get('credit_account_gross_amount_id'), total_gross_amount)))
        move_lines.append((0, 0, self._create_account_move_line("Total Subsidy Amount", 0.0, config_settings.get('total_subsidy_amount'), config_settings.get('subsidy_credit_account_id'), total_subsidy_amount)))
        move_lines.append((0, 0, self._create_account_move_line("Total Shipping Cost", config_settings.get('total_shipping_cost'), 0.0, config_settings.get('debit_account_shipping_id'), total_shipping_cost)))
        move_lines.append((0, 0, self._create_account_move_line("Total Voucher Amount", config_settings.get('total_voucher_amount'), 0.0, config_settings.get('debit_account_voucher_id'), total_voucher_amount)))
        move_lines.append((0, 0, self._create_account_move_line("Total Commission", config_settings.get('total_commission'), 0.0, config_settings.get('debit_account_commission_id'), total_commission)))
        move_lines.append((0, 0, self._create_account_move_line("Total Service Fee", config_settings.get('total_service_fee'), 0.0, config_settings.get('debit_account_service_fee_id'), total_service_fee)))
        move_lines.append((0, 0, self._create_account_move_line("Total Net Amount", config_settings.get('total_net_amount'), 0.0, config_settings.get('debit_account_net_amount_id'), total_net_amount)))

        return move_lines

    def _create_account_move_line(self, name, debit, credit, account_id, total_net_amount):
        # Check if debit or credit is None, and set them to 0.0 if needed
        if debit is None:
            debit = 0.0
        if credit is None:
            credit = 0.0

        # Calculate debit and credit amounts based on total_net_amount
        if debit == 0.0:
            debit = total_net_amount if credit > 0.0 else 0.0
        if credit == 0.0:
            credit = total_net_amount if debit > 0.0 else 0.0

        return {
            'name': name,
            'debit': debit,
            'credit': credit,
            'account_id': account_id,
        }

    def _prepare_invoice_line_data(self, settlement_batch_product_id, journal_id, config_settings):
        return {
            'name': settlement_batch_product_id.name,
            'product_id': settlement_batch_product_id.id,
            'quantity': 1,
            'price_unit': self.total_net_amount,  # Use self.total_net_amount here
            'account_id': self.env['account.account'].browse(config_settings.get('debit_account_net_amount_id')).id,
            # 'account_id': journal_id.default_account_id,
        }

    def _generate_error_response(self, error_message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Error',
                'message': error_message,
                'sticky': False,
            },
        }

    def _generate_success_response(self, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': message,
                'sticky': False,
            },
        }

# Settlement Line Model
class FarmakuSettlementLine(models.Model):
    _name = 'farmaku.settlement.line'
    _description = 'Settlement Line'

    # Fields for the settlement line
    mp_invoice = fields.Char(string='MP Invoice', required=True)
    gross_amount = fields.Monetary(string='Gross Amount', currency_field='currency_id')
    subsidy_amount = fields.Monetary(string='Subsidy Amount', currency_field='currency_id')
    shipping_cost = fields.Monetary(string='Shipping Cost', currency_field='currency_id', default=0)
    voucher_amount = fields.Monetary(string='Voucher Amount', currency_field='currency_id', default=0)
    commission = fields.Monetary(string='Commission', currency_field='currency_id', default=0)
    service_fee = fields.Monetary(string='Service Fee', currency_field='currency_id', default=0)

    # Add a currency field to store the line's currency
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    # Define the many-to-one relationship with the settlement batch
    settlement_batch_id = fields.Many2one('farmaku.settlement.batch', string='Settlement Batch')

    # Add a computed field for net amount
    net_amount = fields.Monetary(string='Net Amount', currency_field='currency_id', compute='_compute_net_amount', store=True)

    @api.depends('gross_amount', 'subsidy_amount', 'shipping_cost', 'voucher_amount', 'commission', 'service_fee')
    def _compute_net_amount(self):
        for line in self:
            net_amount = (
                line.gross_amount +
                line.subsidy_amount -
                line.shipping_cost -
                line.voucher_amount -
                line.commission -
                line.service_fee
            )
            line.net_amount = net_amount
