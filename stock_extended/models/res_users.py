from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    def check_warehouse(self, warehouse_ids):
        if self.property_warehouse_id and warehouse_ids and self.property_warehouse_id.id not in warehouse_ids.ids:
            warehouse_names = ', '.join(warehouse_ids.mapped('display_name'))
            raise ValidationError(_(f'You are not allow to process transfer in warehouse {warehouse_names}'
                                    f'.\nYour default warehouse is {self.property_warehouse_id.display_name}'))
