from odoo import models, fields, api, _
from odoo.exceptions import UserError

class OperatingUnit(models.Model):
    _inherit = 'operating.unit'

    def name_get(self):
        res = []
        for ou in self:
            name = ou.name
            res.append((ou.id, name))
        return res