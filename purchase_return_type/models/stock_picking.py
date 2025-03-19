from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_is_purchase_return(self):
        for rec in self:
            is_purchase_return = False
            if rec.location_dest_id.usage == 'supplier':
                is_purchase_return = True
            rec.is_purchase_return = is_purchase_return

    @api.depends('partner_id.purchase_return_type_id')
    def _get_purchase_return_type_id(self):
        for rec in self:
            if rec.is_purchase_return and rec.partner_id:
                rec.purchase_return_type_id = rec.partner_id.purchase_return_type_id.id

    def _inverse_purchase_return_type_id(self):
        return True
    
    purchase_return_type_id = fields.Many2one(
        comodel_name='purchase.return.type',
        string='Purchase Return Type',
        compute='_get_purchase_return_type_id',
        store=True,
        inverse='_inverse_purchase_return_type_id',
        required=False)
    is_purchase_return = fields.Boolean(
        string='Is Purchase Return',
        compute='_get_is_purchase_return')
