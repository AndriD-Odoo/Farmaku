# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _update_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, line):
        res = super(StockRule, self)._update_purchase_order_line(product_id, product_qty, product_uom, company_id, values, line)
        if product_uom.id != line.product_uom.id:
            price_unit = product_uom._compute_price(res['price_unit'], line.product_uom)
            res['price_unit'] = price_unit
        return res

    def _make_po_get_domain(self, company_id, values, partner):
        rule_ids = self.filtered(lambda r: r.action == 'buy')
        for rule_id in rule_ids:
            if partner.in_type_id:
                in_type_id = partner.in_type_id
            else:
                in_type_id = rule_id.warehouse_id.in_type_id
            # rule_id.sudo().write({'picking_type_id': in_type_id.id})
            rule_id.write({'picking_type_id': in_type_id.id})
        res = super(StockRule, self)._make_po_get_domain(company_id, values, partner)
        return res

    def _prepare_purchase_order(self, company_id, origins, values):
        res = super(StockRule, self)._prepare_purchase_order(company_id=company_id, origins=origins, values=values)
        date_order = res.get('date_order')
        if date_order and date_order < fields.Datetime.now():
            res['date_order'] = fields.Datetime.now()
        return res
