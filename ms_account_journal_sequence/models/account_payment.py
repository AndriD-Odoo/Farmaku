from odoo import fields, models, api, http, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model_create_multi
    def create(self, vals_list):
        payments = super(AccountPayment, self).create(vals_list)
        for i, pay in enumerate(payments):
            print('\n i', i)
            print('\n pay', pay)
            self.env.remove_to_compute(self.env['account.move']._fields['name'], pay.move_id)
        return payments
