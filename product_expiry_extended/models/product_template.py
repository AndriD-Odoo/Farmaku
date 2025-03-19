from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    expiration_time = fields.Integer(default=18*30)  # default 18 bulan

    def _update_expiration_time(self):
        self.env.cr.execute(f"""
            UPDATE
                product_template
            SET
                expiration_time = 18*30
        """)
