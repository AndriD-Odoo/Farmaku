from odoo import api, fields, models
from odoo.exceptions import ValidationError


class UomUom(models.Model):
    _inherit = 'uom.uom'

    def _compute_quantity(self, qty, to_unit, round=True, rounding_method='UP', raise_if_failure=True):
        if self.uom_type == 'bigger' and to_unit.factor == 1:
            qty = qty * self.factor_inv
        else:
            qty = super(UomUom, self)._compute_quantity(
                qty=qty, to_unit=to_unit, round=round, rounding_method=rounding_method, raise_if_failure=raise_if_failure
            )
        return qty
