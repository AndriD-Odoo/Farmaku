from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    additional_partner_ids = fields.Many2many(
        comodel_name='res.partner',
        domain=[('email', '!=', False)],
        string='Additional Recipients')
    additional_partners = fields.Char(
        string='Additional Recipients by Code',
        required=False)

    def get_additional_partners(self, res_id):
        partners = []
        for template_id in self:
            for partner_id in template_id.additional_partner_ids:
                if partner_id.id not in partners:
                    partners.append(partner_id.id)
            if template_id.additional_partners:
                current_val = self.env[template_id.model].browse(res_id)
                additional_partners = template_id.additional_partners.replace(' ', '')
                additional_partners = additional_partners.replace('${object.', '').replace('}', '')
                for attr in additional_partners.split('.'):
                    current_val = getattr(current_val, attr)
                additional_partners = current_val
                if type(additional_partners) != list:
                    additional_partners = [additional_partners]
                partners += additional_partners
        return partners
