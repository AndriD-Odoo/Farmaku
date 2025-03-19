# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import fields, models, api


class CreatePosProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create_pos_product(self, vals):

        rec = self.env['product.product'].create(vals)

        vals['id'] = rec.id
        vals['lst_price'] = vals.get(
            'lst_price') if vals.get('lst_price') else 0
        vals['taxes_id'] = [rec.taxes_id.id]
        vals['create_from_pos'] = True
        vals['uom_id'] = [rec.uom_id.id, rec.uom_id.name]
        # vals['uom_po_id'] = [rec.uom_id.id, rec.uom_id.name]
        vals['pos_categ_id'] = [rec.pos_categ_id.id, rec.pos_categ_id.name]
        vals['product_tmpl_id'] = [rec.product_tmpl_id.id]
        vals['tracking'] = 'none'

        return rec.read()[0]


class PosConfig(models.Model):
    _inherit = 'pos.config'

    create_pos_product = fields.Boolean("Enable Product Creation")
