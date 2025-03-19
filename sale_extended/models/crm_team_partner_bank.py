from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmTeamPartnerBank(models.Model):
    _name = "crm.team.partner.bank"
    _description = "EDC Bank Account"

    team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Sales Team',
        ondelete='cascade')
    edc_id = fields.Many2one(
        comodel_name='electronic.data.capture',
        string='EDC',
        copy=False,
        required=False)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='team_id.company_id',
    )
    company_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Company Partner',
        related='company_id.partner_id',
        check_company=True
    )
    partner_bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        string='Recipient Bank',
        check_company=True,
        required=True,
    )
    payment_method_id = fields.Many2one(
        comodel_name='payment.method',
        string='Payment Method',
        required=False)
    bank_id = fields.Many2one(
        comodel_name='res.bank',
        string='Bank',
        required=False)

    @api.onchange('bank_id')
    def onchange_bank(self):
        self.partner_bank_id = False
