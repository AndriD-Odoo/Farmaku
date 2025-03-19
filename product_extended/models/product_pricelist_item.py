from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    @api.model
    def create(self, values):
        if values.get('pricelist_id') and values.get('product_tmpl_id') and values.get('fixed_price')\
                and values.get('date_start') and values.get('date_end'):
            domain = [
                ('pricelist_id', '=', values['pricelist_id']),
                ('product_tmpl_id', '=', values['product_tmpl_id']),
                ('fixed_price', '=', values['fixed_price']),
            ]
            # case 1
            additional_domain = [
                ('date_end', '>', values['date_start']),
                ('date_end', '>=', values['date_end']),
            ]
            item_id = self.search(domain + additional_domain, limit=1, order='date_end desc')
            if item_id:
                return item_id
            # case 2
            additional_domain = [
                ('date_end', '>=', values['date_start']),
                ('date_end', '<', values['date_end']),
            ]
            item_id = self.search(domain + additional_domain, limit=1, order='date_end desc')
            if item_id:
                item_id.write({'date_end': values['date_end']})
                return item_id
        return super(ProductPricelistItem, self).create(values)
