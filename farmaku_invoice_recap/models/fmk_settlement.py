# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

# Settlement Batch Model
class FarmakuSettlementBatch(models.Model):
    _name = 'farmaku.settlement.batch'
    _description = 'Settlement Batch'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    name = fields.Char(string='Name', required=True, default='Draft')
    sales_team = fields.Many2one('crm.team', string='Sales Team', required=True)
    # team_code = fields.Char(string='Invoice Recap Code', compute='_compute_team_code', store=True)
    team_code = fields.Char(string='Invoice Recap Code', related='sales_team.team_code', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    settlement_line_ids = fields.One2many(
        'farmaku.settlement.line',
        'settlement_batch_id',
        string='Settlement Lines'
    )
    settlement_additions_ids = fields.One2many(
        'farmaku.settlement.additions',
        'settlement_batch_id',
        string='Settlement Additions'
    )
    settlement_deductions_ids = fields.One2many(
        'farmaku.settlement.deductions',
        'settlement_batch_id',
        string='Settlement Deductions'
    )
    total_additions = fields.Monetary(string='Total Additions', compute='_compute_amount', store=True)
    total_deductions = fields.Monetary(string='Total Deductions', compute='_compute_amount', store=True)
    total_net_amount = fields.Monetary(string='Total Net Amount', compute='_compute_amount', store=True)
    total_gross_amount = fields.Monetary(string='Total Gross Amount', compute='_compute_amount', store=True)
    total_gross_amount_after_refunds = fields.Monetary(string='Total Gross Amount After Refunds', compute='_compute_amount', store=True)
    total_subsidy_amount = fields.Monetary(string='Total Subsidy Amount', compute='_compute_amount', store=True)
    total_shipping_cost = fields.Monetary(string='Total Shipping Cost', compute='_compute_amount', store=True)
    total_voucher_amount = fields.Monetary(string='Total Voucher Amount', compute='_compute_amount', store=True)
    total_commission = fields.Monetary(string='Total Commission', compute='_compute_amount', store=True)
    total_service_fee = fields.Monetary(string='Total Service Fee', compute='_compute_amount', store=True)
    total_refund_current_period = fields.Monetary(
        string='Total Refund Current Period',
        compute='_compute_amount',
        store=True,
    )
    total_refund_previous_period = fields.Monetary(
        string='Total Refund Previous Period',
        compute='_compute_amount',
        store=True,
    )
    account_type = fields.Selection(
        [('income', 'Income'), ('expense', 'Expense')],
        string='Account Type',
        required=True,
        default='income',
    )
    invoice_recap_id = fields.Many2one(
        'account.move',
        string='Invoice Recap',
        ondelete='set null', 
        readonly=True,
        default=False
    )


    @api.model
    def create(self, vals):
        if vals.get('name', 'Draft') == 'Draft':
            # Check if the associated sales team has a team_code
            if vals.get('sales_team'):
                sales_team = self.env['crm.team'].browse(vals['sales_team'])
                if not sales_team.team_code:
                    raise ValidationError("Sales Team must have a team_code value.")
                team_code = sales_team.team_code
            else:
                team_code = ''
            
            # Get the next sequence number for settlement batches
            sequence = self.env.ref('farmaku_invoice_recap.sequence_settlement_batch')
            sequence_number = sequence.next_by_id()
            vals['name'] = "{}/{}".format(team_code, sequence_number)
        return super(FarmakuSettlementBatch, self).create(vals)

    @api.depends(
        'settlement_line_ids.refund',
        'settlement_line_ids.is_previous_period',
        'settlement_line_ids.gross_amount',
        'settlement_line_ids.subsidy_amount',
        'settlement_line_ids.shipping_cost',
        'settlement_line_ids.voucher_amount',
        'settlement_line_ids.commission',
        'settlement_line_ids.service_fee',
        'settlement_additions_ids.amount',
        'settlement_deductions_ids.amount',
    )
    def _compute_amount(self):
        for batch in self:
            # Reset all total fields to zero
            batch.total_net_amount = 0.0
            batch.total_gross_amount = 0.0
            batch.total_subsidy_amount = 0.0
            batch.total_shipping_cost = 0.0
            batch.total_voucher_amount = 0.0
            batch.total_commission = 0.0
            batch.total_service_fee = 0.0
            batch.total_additions = 0.0
            batch.total_deductions = 0.0
            batch.total_refund_previous_period = 0.0
            batch.total_refund_current_period = 0.0

            # Calculate the totals based on the current state of records
            total_net_amount = sum(batch.settlement_line_ids.mapped('net_amount'))
            total_gross_amount = sum(batch.settlement_line_ids.mapped('gross_amount'))
            total_subsidy_amount = sum(batch.settlement_line_ids.mapped('subsidy_amount'))
            total_shipping_cost = -sum(batch.settlement_line_ids.mapped('shipping_cost'))
            total_voucher_amount = -sum(batch.settlement_line_ids.mapped('voucher_amount'))
            total_commission = -sum(batch.settlement_line_ids.mapped('commission'))
            total_service_fee = -sum(batch.settlement_line_ids.mapped('service_fee'))

            total_refund_current_period = -sum(
                line.refund for line in batch.settlement_line_ids if not line.is_previous_period
            )

            total_refund_previous_period = -sum(
                line.refund for line in batch.settlement_line_ids if line.is_previous_period
            )

            # Calculate the gross_amount_after_refunds field
            gross_amount_after_refunds = total_gross_amount + total_refund_current_period + total_refund_previous_period

            if batch.settlement_additions_ids:
                batch.total_additions = sum(batch.settlement_additions_ids.mapped('amount'))

            if batch.settlement_deductions_ids:
                batch.total_deductions = -sum(batch.settlement_deductions_ids.mapped('amount'))

            batch.total_net_amount = (
                total_net_amount + batch.total_additions + batch.total_deductions + total_refund_previous_period
            )
            batch.total_gross_amount = total_gross_amount
            batch.total_gross_amount_after_refunds = gross_amount_after_refunds  # Add this line
            batch.total_subsidy_amount = total_subsidy_amount
            batch.total_shipping_cost = total_shipping_cost
            batch.total_voucher_amount = total_voucher_amount
            batch.total_commission = total_commission
            batch.total_service_fee = total_service_fee
            batch.total_refund_previous_period = total_refund_previous_period
            batch.total_refund_current_period = total_refund_current_period

    def action_generate_invoice_recap(self):
        try:
            self._validate_settlement_batch()

            # Retrieve values from the sales_team object
            config_settings = self._get_config_settings()

            missing_parameters = self._check_parameters(config_settings)
            if missing_parameters:
                error_message = "The following parameters are missing or empty:\n"
                error_message += "\n".join(missing_parameters)
                return self._generate_error_response(error_message)

            self._create_batch_payment(config_settings)
            self._create_invoice_recap(config_settings)

            success_message = "Invoice Recap Created successfully."
            return self._generate_success_response(success_message)

        except ValidationError as validation_error:
            return self._generate_error_response(validation_error.name)
        except Exception as create_error:
            return self._generate_error_response(str(create_error))

    def _get_config_settings(self):
        sales_team = self.sales_team
        if not sales_team:
            raise ValidationError("Sales Team is not defined.")

        config_settings = {
            'partner_id': sales_team.partner_id or False,
            'team_code': sales_team.team_code or '',
            'partner_bank_id': sales_team.partner_bank_id or False,
            'payment_journal_id': sales_team.payment_journal_id or False,
            'gross_amount_product_id': sales_team.gross_amount_product_id or False,
            'subsidy_amount_product_id': sales_team.subsidy_amount_product_id or False,
            'shipping_cost_product_id': sales_team.shipping_cost_product_id or False,
            'voucher_amount_product_id': sales_team.voucher_amount_product_id or False,
            'commission_product_id': sales_team.commission_product_id or False,
            'service_fee_product_id': sales_team.service_fee_product_id or False,
            'gross_amount_account_id': sales_team.gross_amount_account_id or False,
            'subsidy_amount_account_id': sales_team.subsidy_amount_account_id or False,
            'shipping_cost_account_id': sales_team.shipping_cost_account_id or False,
            'voucher_amount_account_id': sales_team.voucher_amount_account_id or False,
            'commission_account_id': sales_team.commission_account_id or False,
            'service_fee_account_id': sales_team.service_fee_account_id or False,
        }

        return config_settings

    def _validate_settlement_batch(self):
        for batch in self:
            errors = []

            if not all([batch.start_date, batch.end_date, batch.name, batch.sales_team, batch.currency_id]):
                errors.append("Required fields cannot be empty.")

            # Placeholder for additional validation logic as needed

            if errors:
                error_message = '\n'.join(errors)
                raise ValidationError(error_message)

    def _check_parameters(self, config_settings):
        missing_parameters = []

        parameters = [
            'partner_id',
            'team_code',
            'partner_bank_id',
            'payment_journal_id',
            'gross_amount_product_id',
            'subsidy_amount_product_id',
            'shipping_cost_product_id',
            'voucher_amount_product_id',
            'commission_product_id',
            'service_fee_product_id',
            'gross_amount_account_id',
            'subsidy_amount_account_id',
            'shipping_cost_account_id',
            'voucher_amount_account_id',
            'commission_account_id',
            'service_fee_account_id',
        ]

        for parameter in parameters:
            if not config_settings.get(parameter):
                missing_parameters.append(parameter)

        return missing_parameters

    def _check_batch_invoices(self):
        selected_invoice_ids = {}
        
        for line in self.settlement_line_ids:
            # Check if there are any duplicate mp_invoice values
            domain = [
                ('mp_invoice', '=', line.mp_invoice),
                ('id', '!=', line.id),
                ('settlement_batch_id', '=', self.id),
            ]
            
            if line.is_previous_period:
                # If it's a previous period settlement line, only check duplicates within the same batch
                domain.append(('is_previous_period', '=', True))
            
            duplicates = self.env['farmaku.settlement.line'].search(domain)
            
            if duplicates:
                if line.is_previous_period:
                    raise exceptions.ValidationError("MP Invoice must be unique within the same settlement batch when 'is_previous_period' is True.")
                else:
                    raise exceptions.ValidationError("MP Invoice must be unique.")
            
            # Check if mp_invoice matches an account.move.ref
            move_domain = [
                ('ref', '=', line.mp_invoice),
                ('state', '=', 'posted'),  # Ensure the move is in 'posted' state
                ('team_id', '=', self.sales_team.id),  # Check Sales Team
            ]
            
            if not line.is_previous_period:
                move_domain.append(('payment_state', '=', 'not_paid'))  # Ensure the move is not paid for the current period
            
            matching_moves = self.env['account.move'].search(move_domain)
            
            if not matching_moves:
                raise exceptions.ValidationError("No valid matching Invoice or Refund found for MP Invoice.")

            # Ensure there's only one matching invoice or refund
            if len(matching_moves) != 1:
                raise exceptions.ValidationError("There should be exactly one valid matching Invoice or Refund for MP Invoice.")

            # If it's a refund for the current period, validate the refund amount
            if line.refund > 0:
                refund_moves = self.env['account.move'].search([
                    ('reversed_entry_id', 'in', matching_moves.ids),
                    ('move_type', '=', 'out_refund'),
                    ('state', '=', 'posted'),
                ])
                total_refund = sum(refund_moves.mapped('amount_total'))
                if total_refund != line.refund:
                    raise exceptions.ValidationError("Refund amount does not match the total refund for the current period invoices.")
                
                # Add refund moves IDs to related_account_move_ids
                related_moves = matching_moves + refund_moves
            else:
                # Add matching moves IDs to related_account_move_ids
                related_moves = matching_moves

            line.related_account_move_ids = [(6, 0, related_moves.ids)]

            # Iterate through related moves and add data to selected_invoice_ids
            for move in related_moves:
                selected_invoice_ids[move.id] = {
                    'partner_id': move.partner_id.id,
                    'name': move.name,
                    'amount': move.amount_total,
                }

        return selected_invoice_ids

    def _create_batch_payment(self, config_settings):
        selected_invoice_ids = self._check_batch_invoices()

        for invoice_id, invoice_data in selected_invoice_ids.items():
            partner_id = invoice_data['partner_id']
            invoice_name = invoice_data['name']
            invoice_amount = invoice_data['amount']

            payment_journal = config_settings['payment_journal_id']

            payment_type = 'inbound'  # Default payment type is inbound for invoices
            move = self.env['account.move'].browse(invoice_id)

            if move.move_type == 'out_refund':
                payment_type = 'outbound'  # Payment type for refunds is outbound

            # Check if the invoice or refund has already been paid
            if move.payment_state == 'paid':
                # Log a message or skip the payment creation
                continue

            context = {
                'active_model': 'account.move',
                'active_ids': [invoice_id],
                'active_id': invoice_id,
                'default_payment_type': payment_type,
            }

            register_payments = self.env['account.payment.register'].with_context(context).create({'journal_id': payment_journal.id})
            register_payments._create_payments()

    def _create_invoice_recap(self, config_settings):
        partner_id = config_settings['partner_id']
        current_user = self.env.uid

        # Use the already existing invoice journal as the journal_id, might change in the future
        journal_id = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)

        if not journal_id:
            raise Exception("No default customer invoices journal found.")

        invoice_lines = self._prepare_invoice_lines(journal_id, config_settings)

        # Create the invoice with multiple lines
        invoice_data = {
            'partner_id': partner_id,
            'invoice_date': fields.Date.today(),
            'journal_id': journal_id.id,
            'invoice_line_ids': invoice_lines,
            'state': 'draft',
            'move_type': 'out_invoice',
            'invoice_user_id': current_user,
            'currency_id': self.env.user.company_id.currency_id.id,
            'settlement_batch_id': self.id,
            'team_id': self.sales_team.id,
            'partner_bank_id': self.sales_team.partner_bank_id.id,
        }

        invoice = self.env['account.move'].create(invoice_data)

        self.write({'invoice_recap_id': invoice.id})

    def _prepare_invoice_lines(self, journal_id, config_settings):
        invoice_lines = []

        product_fields = [
            ('total_gross_amount_after_refunds', 'gross_amount_product_id', 'income'),
            ('total_subsidy_amount', 'subsidy_amount_product_id', 'income'),
            ('total_shipping_cost', 'shipping_cost_product_id', 'expense'),
            ('total_voucher_amount', 'voucher_amount_product_id', 'expense'),
            ('total_commission', 'commission_product_id', 'expense'),
            ('total_service_fee', 'service_fee_product_id', 'expense')
        ]

        for field_name, product_field, line_account_type in product_fields:
            product_id = config_settings.get(product_field)
            amount = getattr(self, field_name)

            # Skip lines with 0.0 amount or missing product
            if amount != 0.0 and product_id:
                invoice_line = self._prepare_invoice_line_data(product_id, journal_id, amount, line_account_type)
                invoice_lines.append((0, 0, invoice_line))

        # Process additions
        invoice_lines.extend(self._prepare_addition_invoice_lines(journal_id, config_settings))

        # Process deductions
        invoice_lines.extend(self._prepare_deduction_invoice_lines(journal_id, config_settings))

        return invoice_lines

    def _prepare_addition_invoice_lines(self, journal_id, config_settings):
        invoice_lines = []

        for addition in self.settlement_additions_ids:
            product_id = addition.product_id
            amount = addition.amount
            description = addition.description
            account_id = addition.account_id
            line_account_type = 'income'  # Income for additions

            if amount != 0.0 and product_id and account_id:
                invoice_line = self._prepare_invoice_line_data(product_id, journal_id, amount, line_account_type, description, account_id)
                invoice_lines.append((0, 0, invoice_line))

        return invoice_lines

    def _prepare_deduction_invoice_lines(self, journal_id, config_settings):
        invoice_lines = []

        for deduction in self.settlement_deductions_ids:
            product_id = deduction.product_id
            amount = -deduction.amount  # Negate amount for deductions
            description = deduction.description
            account_id = deduction.account_id
            line_account_type = 'expense'  # Expense for deductions

            if amount != 0.0 and product_id and account_id:
                invoice_line = self._prepare_invoice_line_data(product_id, journal_id, amount, line_account_type, description, account_id)
                invoice_lines.append((0, 0, invoice_line))

        return invoice_lines

    def _prepare_invoice_line_data(self, product_id, journal_id, amount, line_account_type, description=None, account_id=None):
        if not product_id:
            raise Exception("Product not specified for invoice line.")

        # Current dictionary, can be updated as needed
        product_account_mapping = {
            'income': {
                self.sales_team.gross_amount_product_id: self.sales_team.gross_amount_account_id.id,
                self.sales_team.subsidy_amount_product_id: self.sales_team.subsidy_amount_account_id.id,
            },
            'expense': {
                self.sales_team.shipping_cost_product_id: self.sales_team.shipping_cost_account_id.id,
                self.sales_team.voucher_amount_product_id: self.sales_team.voucher_amount_account_id.id,
                self.sales_team.commission_product_id: self.sales_team.commission_account_id.id,
                self.sales_team.service_fee_product_id: self.sales_team.service_fee_account_id.id,
            }
        }

        # Placeholder for additional logic and/or logger for testing

        account_id = account_id or product_account_mapping.get(line_account_type, {}).get(product_id, False)

        if not account_id:
            raise Exception(f"No matching account found for product ID {product_id} and account type {line_account_type}")

        return {
            'name': description or product_id.name,
            'product_id': product_id.id,
            'quantity': 1,
            'price_unit': amount,
            'account_id': account_id,
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

    mp_invoice = fields.Char(string='MP Invoice', required=True)
    gross_amount = fields.Monetary(string='Gross Amount', currency_field='currency_id')
    refund = fields.Monetary(string='Refund', currency_field='currency_id', default=0)
    subsidy_amount = fields.Monetary(string='Subsidy Amount', currency_field='currency_id')
    shipping_cost = fields.Monetary(string='Shipping Cost', currency_field='currency_id', default=0)
    voucher_amount = fields.Monetary(string='Voucher Amount', currency_field='currency_id', default=0)
    commission = fields.Monetary(string='Commission', currency_field='currency_id', default=0)
    service_fee = fields.Monetary(string='Service Fee', currency_field='currency_id', default=0)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    settlement_batch_id = fields.Many2one('farmaku.settlement.batch', string='Settlement Batch', required=True, ondelete='cascade')
    net_amount = fields.Monetary(string='Net Amount', currency_field='currency_id', compute='_compute_net_amount', store=True)
    is_previous_period = fields.Boolean(string='Refund for Past Invoice', default=False)
    # relevant_invoice_id = fields.Many2one('account.move', string='Relevant Invoice')
    # relevant_refund_ids = fields.One2many('account.move', string='Relevant Refund Invoices')
    related_account_move_ids = fields.One2many(
        'account.move',
        'settlement_line_id',
        string='Related Invoices'
    )


    @api.depends('gross_amount', 'subsidy_amount', 'shipping_cost', 'voucher_amount', 'commission', 'service_fee', 'refund', 'is_previous_period')
    def _compute_net_amount(self):
        for line in self:
            if not line.is_previous_period:
                net_amount = (
                    line.gross_amount +
                    line.subsidy_amount -
                    line.shipping_cost -
                    line.voucher_amount -
                    line.commission -
                    line.service_fee -
                    line.refund
                )
                line.net_amount = net_amount
            else:
                # Handle the case where is_previous_period is True
                line.net_amount = 0.0
                line.subsidy_amount = 0.0 
                line.shipping_cost = 0.0
                line.voucher_amount = 0.0
                line.commission = 0.0
                line.service_fee = 0.0

    @api.constrains('mp_invoice', 'refund')
    def _check_mp_invoice(self):
        for record in self:
            # Check if there are any duplicate mp_invoice values
            domain = [('mp_invoice', '=', record.mp_invoice), ('id', '!=', record.id)]
            
            if record.is_previous_period:
                # If it's a previous period settlement line, only check duplicates within the same batch
                domain.append(('settlement_batch_id', '=', record.settlement_batch_id.id))
            
            duplicates = self.search(domain)
            
            if duplicates:
                if record.is_previous_period:
                    raise exceptions.ValidationError("MP Invoice must be unique in the same settlement batch when 'is_previous_period' is True.")
                else:
                    raise exceptions.ValidationError("MP Invoice must be unique.")

            # Check if mp_invoice matches an account.move.ref
            move_domain = [
                ('ref', '=', record.mp_invoice),
                ('move_type', 'in', ['out_invoice', 'out_refund']),  # Ensure it's an invoice or refund
                ('state', '=', 'posted'),  # Ensure the move is in 'posted' state
                ('team_id', '=', record.settlement_batch_id.sales_team.id),  # Check Sales Team
            ]
            
            if not record.is_previous_period:
                move_domain.append(('payment_state', '=', 'not_paid'))  # Ensure the move is not paid for current period
            
            matching_moves = self.env['account.move'].search(move_domain)
            
            if not matching_moves:
                raise exceptions.ValidationError("No valid matching Invoice or Refund found for MP Invoice.")

            # Ensure there's only one matching invoice or refund
            if len(matching_moves) != 1:
                raise exceptions.ValidationError("There should be exactly one valid matching Invoice or Refund for MP Invoice.")

            # If it's a refund for the current period, validate the refund amount
            if record.refund > 0:
                refund_moves = self.env['account.move'].search([
                    ('reversed_entry_id', 'in', matching_moves.ids),
                    ('move_type', '=', 'out_refund'),
                    ('state', '=', 'posted'),
                ])
                total_refund = sum(refund_moves.mapped('amount_total'))
                if total_refund != record.refund:
                    raise exceptions.ValidationError("Refund amount does not match the total refund for the current period invoices.")
                
                # Add refund moves IDs to related_account_move_ids
                related_moves = matching_moves + refund_moves
            else:
                # Add matching moves IDs to related_account_move_ids
                related_moves = matching_moves

            record.related_account_move_ids = [(6, 0, related_moves.ids)]


# Model for Settlement Additions
class FarmakuSettlementAdditions(models.Model):
    _name = 'farmaku.settlement.additions'
    _description = 'Settlement Additions'

    description = fields.Char(string='Description', required=True)
    amount = fields.Float(string='Amount', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    account_id = fields.Many2one('account.account', string='Account', required=True)
    settlement_batch_id = fields.Many2one('farmaku.settlement.batch', string='Settlement Batch', ondelete='cascade')

    @api.constrains('amount')
    def _check_amount_positive(self):
        for record in self:
            if record.amount < 0:
                raise exceptions.ValidationError("Amount cannot be negative for Settlement Additions.")

# Model for Settlement Deductions
class FarmakuSettlementDeductions(models.Model):
    _name = 'farmaku.settlement.deductions'
    _description = 'Settlement Deductions'

    description = fields.Char(string='Description', required=True)
    amount = fields.Float(string='Amount', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    account_id = fields.Many2one('account.account', string='Account', required=True)
    settlement_batch_id = fields.Many2one('farmaku.settlement.batch', string='Settlement Batch', ondelete='cascade')

    @api.constrains('amount')
    def _check_amount_positive(self):
        for record in self:
            if record.amount < 0:
                raise exceptions.ValidationError("Amount cannot be negative for Settlement Deductions.")
