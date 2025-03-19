# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import pandas as pd
import io
import base64
import logging

_logger = logging.getLogger(__name__)

class WizardImportBankExcel(models.TransientModel):
    _name = 'wizard.import.bank.excel'
    _description = "Wizard import bank excel"

    inv_excel_file = fields.Binary("Excel File")
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', domain=[('type', '=', 'bank')], required=True, default=lambda self: self.env['account.journal'].search([('type', '=', 'bank')], limit=1))

    def action_read_excel(self):
        self.ensure_one()
        file_path = base64.decodebytes(self.inv_excel_file)

        # Read the Excel file
        try:
            df = pd.read_excel(io.BytesIO(file_path), usecols=['mp_invoice', 'gross_amount', 'date', 'team_code'])

            invoice_numbers = []
            payments_to_create = []
            invoices_to_update = []

            for index, row in df.iterrows():
                invoice_number = row['mp_invoice']
                total_amount = row['gross_amount']
                paid_date = row['date']
                batch_no = row['team_code']

                # Search for the invoice in account.move
                invoice = self.env['account.move'].search([('ref', '=', invoice_number)], limit=1)

                if invoice:
                    if invoice.amount_total == total_amount:
                        if invoice_number in invoice_numbers:
                            df.loc[index, 'Check MP'] = 'MP Invoice Duplicate'
                            continue
                        else:
                            invoice_numbers.append(invoice_number)
                            invoice.message_post(body=f'Found invoice: {invoice.ref} with total amount: {total_amount}, Reconciled on {batch_no}')
                            invoice.narration = batch_no

                        # Prepare payment data
                        payment_data = {
                            'amount': total_amount,
                            'payment_type': 'inbound',
                            'partner_type': 'customer',
                            'partner_id': invoice.partner_id.id,
                            'ref': invoice.name,
                            'date': paid_date,
                            'journal_id': self.bank_journal_id.id or self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id,
                            'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                            'reconciled_invoice_ids': [(6, 0, [invoice.id])],
                        }
                        payments_to_create.append(payment_data)
                        invoices_to_update.append(invoice)

                    else:
                        df.loc[index, 'Check Total'] = 'Amount is not Match'
                else:
                    df.loc[index, 'Check MP'] = 'MP Invoice is not found'

            # Process payments in batches to reduce server load
            batch_size = 100  # Number of payments to process per batch
            for i in range(0, len(payments_to_create), batch_size):
                batch = payments_to_create[i:i + batch_size]
                payments = self.env['account.payment'].create(batch)
                payments.action_post()

            # Bulk update invoices after payments are processed
            invoice_ids = [inv.id for inv in invoices_to_update]
            invoices_to_write = self.env['account.move'].browse(invoice_ids)
            invoices_to_write.write({
                'payment_state': 'paid',
                'amount_residual': 0.0,
                'amount_residual_signed': 0.0,
            })

            # return message to invoices (after bulk payment success)
            failed_invoices = []

            for invoice, payment in zip(invoices_to_update, payments):
                if invoice and payment:  # Cek validitas data
                    try:
                        invoice.sudo().message_post(
                            body=f'Payment has been posted on <a href="/web#id={payment.id}&model=account.payment&view_type=form">{payment.name}</a>',
                            message_type='comment',
                            subtype_xmlid='mail.mt_comment',
                        )
                    except Exception as e:
                        _logger.error(f"Failed to post message on invoice {invoice.id}: {str(e)}")
                        failed_invoices.append(invoice.id)

            # Log data yang gagal
            if failed_invoices:
                _logger.warning(f"Invoices that failed to post messages: {failed_invoices}")


            # Save the modified DataFrame back to Excel
            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            return {
                'type': 'ir.actions.act_url',
                'url': 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,' + base64.b64encode(output.getvalue()).decode(),
                'target': 'self',
            }

        except Exception as e:
            raise UserError(f'Error reading Excel file: {str(e)}')