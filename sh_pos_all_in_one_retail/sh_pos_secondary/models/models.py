# Copyright (C) Softhealer Technologies.
from odoo import fields,models,api


class POSOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @api.model
    def create(self, values):
        product_id = self.env['product.product'].browse(values['product_id'])
        if 'product_id' in values and not values.get('secondary_uom_id'):
            values['secondary_uom_id'] = product_id.sh_secondary_uom.id
        return super(POSOrderLine, self).create(values)

    def write(self, values):
        if 'product_id' in values and not values.get('secondary_uom_id'):
            product_id = self.env['product.product'].browse(values['prodsh_pos_all_in_one_retailuct_id'])
            values['secondary_uom_id'] = product_id.sh_secondary_uom.id
        res = super(POSOrderLine, self).write(values)
        return res
    
    secondary_qty = fields.Float("Secondary Qty")
    secondary_uom_id = fields.Many2one('uom.uom', string="Secondary UOM")


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_enable_seconadry = fields.Boolean(string="Enable Change UOM Feature")
    select_uom_type = fields.Selection([('primary', 'Primary'), ('secondary', 'Secondary')], string='Select Default UOM type', default='primary')
    display_uom_in_receipt = fields.Boolean(string='Display UOM in Receipt')
    enable_price_to_display = fields.Boolean(string='Display price in Secondary UOM ?')