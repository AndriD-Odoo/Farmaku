from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        value = super().onchange_template_id(template_id=template_id, composition_mode=composition_mode, model=model,
                                             res_id=res_id)
        partner_ids = value.get('value', {}).get('partner_ids', [])
        trx_id = self.env[model].browse(res_id)
        for partner_id in trx_id.message_partner_ids:
            if partner_id.id not in partner_ids and partner_id.id != self.env.user.partner_id.id:
                partner_ids.append(partner_id.id)
        template_id = self.env['mail.template'].browse(template_id)
        additional_partners = template_id.get_additional_partners(res_id=res_id)
        for p_id in additional_partners:
            if p_id not in partner_ids:
                partner_ids.append(p_id)
        value['partner_ids'] = partner_ids
        return value

    def get_mail_values(self, res_ids):
        results = super().get_mail_values(res_ids)
        for res_id, value in results.items():
            additional_partners = self.template_id.get_additional_partners(res_id=res_id)
            if additional_partners:
                additional_partner_ids = self.env['res.partner'].browse(additional_partners)
                additional_partner_ids = additional_partner_ids.filtered(lambda p: p.id in self.partner_ids.ids)
                emails = ', '.join(additional_partner_ids.mapped('email'))
                value['email_cc'] = emails
        return results
