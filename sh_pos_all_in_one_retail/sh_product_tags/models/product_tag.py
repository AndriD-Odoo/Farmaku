# -*- coding: utf-8 -*-

from odoo import models, fields, api


class productTag(models.Model):
    _name = "sh.product.tag"
    _description = 'Product Tag'
    _order = 'sequence asc'

    name = fields.Char('Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=0, index=True, required=True)
    color = fields.Integer(
        string='Color Index',
        help="Color to apply to this tag (including in website).")

    product_ids = fields.Many2many('product.template',
                                   'sh_product_tmpl_tag_rel',
                                   'tag_id',
                                   'product_id',
                                   string='Products')
