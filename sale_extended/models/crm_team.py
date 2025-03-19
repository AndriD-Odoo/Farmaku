from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    edc_bank_ids = fields.One2many(
        comodel_name='crm.team.partner.bank',
        inverse_name='team_id',
        string='EDC Bank',
        required=False)
    partner_bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        string='Default Recipient Bank',
        check_company=True,
        required=True,
    )
    is_pos = fields.Boolean(
        string='Is From POS',
        required=False)
