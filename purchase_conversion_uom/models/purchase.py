import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from odoo.tools.float_utils import float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _add_supplier_to_product(self):
        company_ids = self.env['res.company'].sudo().search([])
        company_partner_ids = company_ids.partner_id
        _logger.info(f'\n company_partner_ids: {company_partner_ids}')
        if self.partner_id.id in company_partner_ids.ids:
            return False
        # tambahan dari module purchase_discount
        po_line_map = {
            line.product_id.product_tmpl_id.id: line for line in self.order_line
        }
        self = self.with_context(po_line_map=po_line_map)

        # Add the partner in the supplier list of the product if the supplier is not registered for
        # this product. We limit to 10 the number of suppliers for a product to avoid the mess that
        # could be caused for some generic products ("Miscellaneous").
        for line in self.order_line:
            # Do not add a contact as a supplier
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            if line.product_id:
                # Convert the price in the right currency.
                currency = partner.property_purchase_currency_id or self.company_id.currency_id
                price = self.currency_id._convert(line.price_unit, currency, line.company_id, line.date_order or fields.Date.today(), round=False)
                # Compute the price for the template's UoM, because the supplier's UoM is related to that UoM.
                if line.product_id.product_tmpl_id.uom_id != line.product_uom:
                    default_uom = line.product_id.product_tmpl_id.uom_id
                    price = line.product_uom._compute_price(price, default_uom)
                vals = {
                    'name': partner.id,
                    'product_tmpl_id': line.product_id.product_tmpl_id.id,
                    'price': price,
                    'currency_id': currency.id,
                    'company_id': self.company_id.id,
                    'date': self.date_order,
                    'discount': line.discount,
                    'last_po_qty': round(line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)),
                }
                seller_id = self.env['product.supplierinfo'].sudo().search([
                    ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                    ('name', '=', partner.id),
                    ('company_id', '=', self.company_id.id),
                ], limit=1)
                if not seller_id:
                    self.env['product.supplierinfo'].sudo().create(vals)
                else:
                    seller_id.sudo().write(vals)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        res = super(PurchaseOrderLine, self)._onchange_quantity()
        if self.product_id:
            params = {'order_id': self.order_id}
            seller = self.product_id.with_company(self.order_id.company_id)._select_seller(
                partner_id=self.partner_id,
                quantity=self.product_qty,
                date=self.order_id.date_order and self.order_id.date_order.date(),
                uom_id=self.product_uom,
                params=params)
            if seller:
                price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                                     self.product_id.supplier_taxes_id,
                                                                                     self.taxes_id,
                                                                                     self.company_id)
                if price_unit and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
                    price_unit = seller.currency_id._convert(
                        price_unit, self.order_id.currency_id, self.order_id.company_id,
                        self.date_order or fields.Date.today())

                price_unit = self.product_id.uom_id._compute_price(price_unit, self.product_uom)

                self.price_unit = price_unit
        return res

    def _suggest_quantity(self):
        res = super(PurchaseOrderLine, self)._suggest_quantity()
        if self.product_id:
            seller_min_qty = self.product_id.seller_ids \
                .filtered(
                lambda r: r.name == self.order_id.partner_id and (not r.product_id or r.product_id == self.product_id)) \
                .sorted(key=lambda r: r.min_qty)
            if seller_min_qty:
                self.product_uom = self.product_id.uom_po_id.id
        return res

    def write(self, values):
        res = super(PurchaseOrderLine, self).write(values)
        for rec in self:
            if ('price_unit' in values or 'product_qty' in values or
                    'product_uom' in values and not self.env.context.get('force_write_pol')):
                rec.order_id.with_context(force_write_pol=True)._add_supplier_to_product()
        return res

    @api.model
    def create(self, values):
        res = super(PurchaseOrderLine, self).create(values)
        if not self.env.context.get('force_write_pol'):
            res.order_id.with_context(force_write_pol=True)._add_supplier_to_product()
        return res
