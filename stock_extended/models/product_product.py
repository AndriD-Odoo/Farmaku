from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _update_tracking_product(self, limit):
        query_limit = ''
        if limit:
            query_limit = f' LIMIT {limit} '
        self.env.cr.execute(f"""
            UPDATE
                product_template
            SET
                tracking = 'lot',
                use_expiration_date = TRUE
            WHERE
                id IN (SELECT id FROM product_TEMPLATE WHERE type = 'product' AND tracking != 'lot' {query_limit})
        """)
