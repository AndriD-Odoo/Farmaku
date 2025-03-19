from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError

class UoM(models.Model):
    _inherit = 'uom.uom'

    is_uom_inventory = fields.Boolean(string='UoM Inventory ?')

    # def _compute_quantity(self, qty, to_unit, round=True, rounding_method='UP', raise_if_failure=True):
    #     if not self:
    #         return qty
    #     self.ensure_one()
    #     if self.category_id.id != to_unit.category_id.id:
    #         if raise_if_failure:
    #             raise UserError(_('The unit of measure %s defined on the order line doesn\'t belong to the same category as the unit of measure %s defined on the product. Please correct the unit of measure defined on the order line or on the product, they should belong to the same category.') % (self.name, to_unit.name))
    #         else:
    #             return qty
    #     amount = qty / self.factor
    #
    #     conv = self._context.get('conversion', 0.0)
    #     conv_value = conv and (1.0 / conv) or 0.0
    #
    #     if conv and not ((self.is_uom_inventory and self.factor == 1.0) or self.uom_type == 'reference'):
    #         conv_value = conv
    #
    #     if conv and to_unit:
    #         amount = qty * conv_value
    #     elif to_unit:
    #         amount = amount * to_unit.factor
    #         if round:
    #             amount = tools.float_round(amount, precision_rounding=to_unit.rounding, rounding_method=rounding_method)
    #     return amount

    # def _compute_price(self, price, to_unit):
    #     self.ensure_one()
    #     conv = self._context.get('conversion', 0)
    #     if (not self or not price or not to_unit) or conv == 0:
    #         return price
    #     if self.category_id.id != to_unit.category_id.id:
    #         return price
    #     amount = price * self.factor
    #     conv_value = conv and (1.0 / conv) or 0.0
    #     if conv and to_unit:
    #         amount = amount / conv_value
    #     elif to_unit:
    #         amount = amount / to_unit.factor
    #     return amount
