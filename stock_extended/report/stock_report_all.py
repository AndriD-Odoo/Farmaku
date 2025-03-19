# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.osv.expression import AND, expression


class PurchaseReport(models.Model):
    _name = "stock.report.all"
    _description = "Inventory Report All Companies"
    _auto = False
    _rec_name = 'product_id'
    _order = 'id asc'

    product_id = fields.Many2one(
        'product.product', 'Product',
        ondelete='restrict', readonly=True, required=True, index=True, check_company=True)
    product_tmpl_id = fields.Many2one(
        'product.template', string='Product Template')
    product_uom_id = fields.Many2one(
        'uom.uom', 'UoM',
        readonly=True)
    company_id = fields.Many2one(string='Company', comodel_name='res.company')
    location_id = fields.Many2one(
        'stock.location', 'Location',
        auto_join=True, ondelete='restrict', readonly=True, required=True, index=True, check_company=True)
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number', index=True,
        ondelete='restrict', readonly=True, check_company=True)
    package_id = fields.Many2one(
        'stock.quant.package', 'Package',
        help='The package containing this quant', readonly=True, ondelete='restrict', check_company=True)
    owner_id = fields.Many2one(
        'res.partner', 'Owner',
        help='This is the owner of the quant', readonly=True, check_company=True)
    quantity = fields.Float(
        'Quantity', digits='Product Unit of Measure Integer',
        help='Quantity of products in this quant, in the default unit of measure of the product',
        readonly=True)
    inventory_quantity = fields.Float(
        'Qty Fisik',
        digits='Product Unit of Measure Integer')
    reserved_quantity = fields.Float(
        'Reserved Quantity',
        default=0.0,
        help='Quantity of reserved products in this quant, in the default unit of measure of the product',
        readonly=True, required=True)
    available_quantity = fields.Float(
        'Available',
        help="On hand quantity which hasn't been reserved on a transfer, in the default unit of measure of the product",
        digits='Product Unit of Measure Integer')
    in_date = fields.Datetime('Incoming Date', readonly=True)
    product_code = fields.Char(string='Product Code')
    expiration_date = fields.Datetime(
        string='Expiration Date'
    )
    use_expiration_date = fields.Boolean(string='Use Expiration Date')

    @property
    def _table_query(self):
        query = '%s %s %s %s' % (self._select(), self._from(), self._where(), self._group_by())

        zero_query = """
            SELECT
                pp.id as product_id,
                pp.product_tmpl_id,
                pt.uom_id as product_uom_id,
                w.company_id,
                w.lot_stock_id as location_id,
                spl.id as lot_id,
                null as package_id,
                null as owner_id,
                0 as quantity,
                0 as inventory_quantity,
                0 as reserved_quantity,
                0 as available_quantity,
                null as in_date,
                pp.default_code as product_code,
                null as expiration_date,
                pt.use_expiration_date
            FROM
            product_product pp
                left join product_template pt on (pt.id=pp.product_tmpl_id)
                left join stock_warehouse w on (1=1)
                left join stock_quant q on (pp.id=q.product_id and w.lot_stock_id=q.location_id)
                left join stock_production_lot spl
                    on spl.product_id = pp.id and w.company_id = spl.company_id
                       and spl.id = (
                            select id
                            from stock_production_lot spl1
                            where spl1.product_id = pp.id and w.company_id = spl1.company_id
                            order by create_date desc
                            limit 1
                         )
            WHERE
                pt.type = 'product'
                and q.id is null
                and pp.active is true
        """

        final_query = f"""
            SELECT
                row_number() OVER () AS id,
                product_id,
                product_tmpl_id,
                product_uom_id,
                company_id,
                location_id,
                lot_id,
                package_id,
                owner_id,
                quantity,
                inventory_quantity,
                reserved_quantity,
                available_quantity,
                in_date,
                product_code,
                expiration_date,
                use_expiration_date
            FROM
                ({query} union {zero_query}) as stock_report_all
            ORDER BY
                CASE WHEN quantity > 0 THEN 1 
                    WHEN quantity <= 0 THEN 2
                END ASC
        """
        return final_query

    def _select(self):
        select_str = """
            SELECT
                q.product_id,
                pp.product_tmpl_id,
                pt.uom_id as product_uom_id,
                q.company_id,
                q.location_id,
                q.lot_id,
                q.package_id,
                q.owner_id,
                q.quantity,
                q.quantity as inventory_quantity,
                q.reserved_quantity,
                q.available_quantity,
                q.in_date,
                q.product_code,
                q.expiration_date,
                pt.use_expiration_date
        """
        return select_str

    def _from(self):
        from_str = """
            FROM
            stock_quant q
                left join product_product pp on (pp.id=q.product_id)
                left join product_template pt on (pt.id=pp.product_tmpl_id)
                left join stock_production_lot spl on (spl.id = q.lot_id)
        """.format(
            currency_table=self.env['res.currency']._get_query_currency_table({'multi_company': True, 'date': {'date_to': fields.Date.today()}}),
        )
        return from_str

    def _where(self):
        return """
            WHERE
                1 = 1
        """

    def _group_by(self):
        group_by_str = """
            
        """
        return group_by_str

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        self = self.sudo()
        return super(PurchaseReport, self)._search(args, offset=offset, limit=limit, order=order, count=count,
                                                   access_rights_uid=access_rights_uid)
