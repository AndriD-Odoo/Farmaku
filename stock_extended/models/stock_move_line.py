from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.depends(
        'product_id',
        'location_id',
    )
    def _get_allowed_lots(self):
        for rec in self:
            domain = [
                ('product_id', '=', rec.product_id.id),
                ('company_id', '=', rec.company_id.id),
            ]
            if rec.location_id.usage != 'internal':
                allowed_lot_ids = self.env['stock.production.lot'].search(domain)
            else:
                domain += [
                    ('location_id', 'child_of', rec.location_id.ids)
                ]
                quant_ids = self.env['stock.quant'].search(domain)
                allowed_lot_ids = quant_ids.mapped('lot_id')
            rec.allowed_lot_ids = allowed_lot_ids

    product_uom_qty = fields.Float(digits='Product Unit of Measure Integer')
    qty_done = fields.Float(digits='Product Unit of Measure Integer')
    move_quantity_done = fields.Float(
        string='Move Quantity Done',
        related='move_id.quantity_done')
    move_reserved_availability = fields.Float(
        string='Move Reserved Availability',
        related='move_id.reserved_availability')
    expiration_date = fields.Datetime(compute=False, string='ED')
    product_expiration_date = fields.Datetime(compute='get_product_expiration_date')
    expiration_month = fields.Char(
        string='Expiration Month(s)',
        compute='_get_expiration_month',
        store=True)
    picking_origin = fields.Char(
        string='Source Document',
        related='picking_id.origin',
        store=True)
    allowed_lot_ids = fields.Many2many(
        comodel_name='stock.production.lot',
        compute='_get_allowed_lots',
        compute_sudo=True,
        string='Allowed Lots')
    product_uom_id = fields.Many2one(string='UoM')

    @api.onchange('expiration_date', 'product_id')
    def onchange_lot_name(self):
        lot_name = False
        if self.picking_id.purchase_id and self.product_id.tracking != 'none':
            if self.picking_id.picking_type_id.use_create_lots:
                barcode = self.product_id.barcode or ''
                if not self.expiration_date:
                    lot_name = f'{barcode}/'
                else:
                    expiration_year = str(self.expiration_date.year)[2:4]
                    lot_name = f"{barcode}/{'{0:02}'.format(self.expiration_date.month)}{'{0:02}'.format(int(expiration_year))}"
        self.lot_name = lot_name

    @api.onchange('product_id', 'product_uom_id')
    def _onchange_product_id(self):
        res = super()._onchange_product_id()
        if self.picking_type_use_create_lots:
            self.expiration_date = False
        return res

    @api.depends('product_id.expiration_time', 'expiration_date')
    def get_product_expiration_date(self):
        for line in self:
            if line.expiration_date:
                line.product_expiration_date = fields.Datetime.today() + timedelta(days=line.product_id.expiration_time)
            else:
                line.product_expiration_date = False

    @api.depends('expiration_date')
    def _get_expiration_month(self):
        for rec in self:
            if rec.expiration_date:
                expiration_days = abs((rec.expiration_date - fields.Datetime.today()).days)
                months, days = divmod(expiration_days, 30)
                if rec.expiration_date < fields.Datetime.today():
                    months = -abs(months)
                    days = -abs(days)
                if months and days:
                    expiration_month_label = f'{months} months {days} days'
                elif months and not days:
                    expiration_month_label = f'{months} months'
                elif not months and days:
                    expiration_month_label = f'{days} days'
                else:
                    expiration_month_label = ''
                rec.expiration_month = expiration_month_label

    def write(self, values):
        res = super(StockMoveLine, self).write(values)
        for rec in self:
            rec.move_id.check_done_qty()
        return res

    @api.model
    def create(self, values):
        res = super(StockMoveLine, self).create(values)
        res.move_id.check_done_qty()
        return res
