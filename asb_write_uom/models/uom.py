from odoo import models, fields, api, _
from odoo.exceptions import UserError

class UomUom(models.Model):
    _inherit = 'uom.uom'

    def action_write_uom(self):
        for rec in self:
            factor = 1
            query = """
                UPDATE uom_uom SET
                        factor = %s
                    WHERE id = %s
                """
            rec.env.cr.execute(query, [factor, rec.id])