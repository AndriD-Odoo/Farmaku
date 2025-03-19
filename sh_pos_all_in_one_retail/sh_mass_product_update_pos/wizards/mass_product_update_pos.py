# Copyright (C) Softhealer Technologies.

from odoo import api, fields, models


class ShMassProductUpdatePosWizard(models.TransientModel):
    _name = 'sh.mass.product.update.pos.wizard'
    _description = 'Mass Product Update Pos'

    name = fields.Boolean('Update Internal Categories')
    product_category = fields.Many2one(
        'product.category', string='Product Category')
    pos_categ_id = fields.Boolean('Update POS Category')
    update_categ_id = fields.Many2one('pos.category', string="POS Category")
    overwrite = fields.Boolean('Overwrite')
    product_lines = fields.Many2many(
        'product.template', string='Mass Product Update')

    @api.model
    def default_get(self, fields):
        res = super(ShMassProductUpdatePosWizard, self).default_get(fields)
        if self.env.context.get('active_ids'):
            res.update({
                'product_lines': [(6, 0, self.env.context.get('active_ids'))],
            })
        return res

    def update_pos_category(self):
        if self.name or self.product_category:
            for line in self.product_lines:
                line.categ_id = self.product_category.id

        if self.pos_categ_id and self.update_categ_id:
            if self.overwrite:
                for line in self.product_lines:
                    line.pos_categ_id = self.update_categ_id.id
            else:
                for line in self.product_lines:
                    if not line.pos_categ_id:
                        line.pos_categ_id = self.update_categ_id.id
