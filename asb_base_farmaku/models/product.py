from odoo import models, fields, api
from odoo.osv import expression


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand', string='Brand')
    product_dot_color_id = fields.Many2one('product.dot.color', string='Dot Color')
    product_type_id = fields.Many2one('product.type', string='Product Type ID')
    forconcoction = fields.Char(string='For Concoction')
    forprescription = fields.Char(string='For Prescription')
    attention = fields.Text(string='Attention')
    contraindication = fields.Text(string='Contraindication')

    dimension_length = fields.Float(string='Dimension Length')
    dimension_height = fields.Float(string='Dimension Height')
    dimension_width = fields.Float(string='Dimension Width')

    dosage = fields.Char(string='Dosage')
    drug_interaction = fields.Char(string='Drug Interaction')
    how_to_use = fields.Text(string='How To Use')
    indication = fields.Text(string='Indication')
    
    is_backorder = fields.Boolean(string='Back Order ?')
    is_fullfilled_bymitra = fields.Boolean(string='Full Filled By Mitra ?')

    long_description = fields.Text(string='Long Description')
    principal_id = fields.Many2one('principal.principal', string='Principal')
    side_effect = fields.Text(string='Side Effect')

    conversion = fields.Integer(string='Conversion')
    conversion_operator = fields.Char(string='Conversion Operator')

    is_best_selling = fields.Boolean(string='Best Selling ?')
    is_new_arrival = fields.Boolean(string='New Arrival ?')
    is_top_offer = fields.Boolean(string='Top Offer ?')
    is_discontinue = fields.Boolean(string='Discontinue ?')

    product_key = fields.Char(string='Product Key')
    meta_keyword = fields.Char(string='Meta Keyword')
    meta_description = fields.Text(string='Meta Description')

    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')


class ProductPhotos(models.Model):
    _name = 'product.photos'
    _description = 'Product Photos'

    image_url = fields.Char(string='Image Url')
    product_id = fields.Many2one('product.product', string='Product')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')


class ProductDotColor(models.Model):
    _name = 'product.dot.color'
    _description = 'Product Dot Color'

    name = fields.Char(string='Name')

    active = fields.Boolean(string='Active', default=True)
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')


class ProductType(models.Model):
    _name = 'product.type'
    _description = 'Product Type'

    name = fields.Char(string='Name')

    active = fields.Boolean(string='Active')
    is_deleted = fields.Boolean(string='Deleted')
    db_note = fields.Text(string='DB Note')
    ethical = fields.Boolean(
        string='Ethical',
        default=True)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_domain_locations_new(self, location_ids, company_id=False, compute_child=True):
        def _search_ids(model, values):
            ids = set()
            domain = []
            for item in values:
                if isinstance(item, int):
                    ids.add(item)
                else:
                    domain = expression.OR([[('complete_name', 'ilike', item)], domain])
            if domain:
                ids |= set(self.env[model].search(domain).ids)
            return ids

        location = self.env.context.get('location')

        if location:
            if not isinstance(location, list):
                location = [location]
            location_ids.update(_search_ids('stock.location', location))

        return super(ProductProduct, self)._get_domain_locations_new(location_ids=location_ids, company_id=company_id, compute_child=compute_child)


class ProductMoveCategory(models.Model):
    _name = "product.move.category"
    _description = "Product Move Category"
    _rec_name = 'category'

    @api.depends('sale_last_30_days', 'category')
    def _get_sale_last_30_days_label(self):
        for rec in self:
            if rec.category == 'fast':
                sale_last_30_days_label = f'> {int(rec.sale_last_30_days)}'
            elif rec.category == 'slow':
                sale_last_30_days_label = f'< {int(rec.sale_last_30_days)}'
            else:
                slow_category_id = self.env.ref('asb_base_farmaku.product_move_category_slow')
                fast_category_id = self.env.ref('asb_base_farmaku.product_move_category_fast')
                sale_last_30_days_label = f'{int(slow_category_id.sale_last_30_days)} - ' \
                                    f'{int(fast_category_id.sale_last_30_days)}'
            rec.sale_last_30_days_label = sale_last_30_days_label

    category = fields.Selection(
        string='Product Move Category',
        selection=[
            ('fast', 'Fast'),
            ('medium', 'Medium'),
            ('slow', 'Slow'),
        ], required=True)
    sale_last_30_days = fields.Float(
        string='Count Sales Last 30 D Input',
        required=True,
    )
    sale_last_30_days_label = fields.Char(
        string='Count Sales Last 30 D',
        compute='_get_sale_last_30_days_label',
        store=True,
    )
    min_buffer = fields.Float(
        string='Min Buffer (days)',
        required=True)
    max_buffer = fields.Float(
        string='Max Buffer (days)',
        required=True)

    def write(self, values):
        res = super(ProductMoveCategory, self).write(values)
        if 'sale_last_30_days' in values:
            medium_category_id = self.env.ref('asb_base_farmaku.product_move_category_medium')
            medium_category_id._get_sale_last_30_days_label()
        return res
