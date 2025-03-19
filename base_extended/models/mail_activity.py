from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    @api.model
    def create(self, vals):
        try:
            res = super(MailActivity, self).create(vals)
        except Exception as e:
            self = self.sudo()
            res = super(MailActivity, self).create(vals)
        return res
