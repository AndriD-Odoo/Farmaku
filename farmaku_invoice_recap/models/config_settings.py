# -*- coding: utf-8 -*-

from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sequence_format = fields.Char(
        string='Settlement Batch Sequence Format',
        config_parameter='farmaku.settlement.batch.sequence_format',
        help='Define the format for settlement batch names using placeholders.'
    )

    gross_amount_product_id = fields.Many2one('product.product', string='Product for Gross Amount')
    subsidy_amount_product_id = fields.Many2one('product.product', string='Product for Subsidy Amount')
    shipping_cost_product_id = fields.Many2one('product.product', string='Product for Shipping Cost')
    voucher_amount_product_id = fields.Many2one('product.product', string='Product for Voucher Amount')
    commission_product_id = fields.Many2one('product.product', string='Product for Commission')
    service_fee_product_id = fields.Many2one('product.product', string='Product for Service Fee')

    # Include any other custom settings fields you need

    def set_values(self):
        # Set the values for your custom settings fields
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('farmaku.settlement.batch.gross_amount_product_id', self.gross_amount_product_id.id)
        self.env['ir.config_parameter'].sudo().set_param('farmaku.settlement.batch.subsidy_amount_product_id', self.subsidy_amount_product_id.id)
        self.env['ir.config_parameter'].sudo().set_param('farmaku.settlement.batch.shipping_cost_product_id', self.shipping_cost_product_id.id)
        self.env['ir.config_parameter'].sudo().set_param('farmaku.settlement.batch.voucher_amount_product_id', self.voucher_amount_product_id.id)
        self.env['ir.config_parameter'].sudo().set_param('farmaku.settlement.batch.commission_product_id', self.commission_product_id.id)
        self.env['ir.config_parameter'].sudo().set_param('farmaku.settlement.batch.service_fee_product_id', self.service_fee_product_id.id)
        self.env['ir.config_parameter'].sudo().set_param('farmaku.settlement.batch.sequence_format', self.sequence_format)

    @api.model
    def get_values(self):
        # Get the values for your custom settings fields
        res = super(ResConfigSettings, self).get_values()
        gross_amount_product_id = self.env['ir.config_parameter'].sudo().get_param('farmaku.settlement.batch.gross_amount_product_id')
        subsidy_amount_product_id = self.env['ir.config_parameter'].sudo().get_param('farmaku.settlement.batch.subsidy_amount_product_id')
        shipping_cost_product_id = self.env['ir.config_parameter'].sudo().get_param('farmaku.settlement.batch.shipping_cost_product_id')
        voucher_amount_product_id = self.env['ir.config_parameter'].sudo().get_param('farmaku.settlement.batch.voucher_amount_product_id')
        commission_product_id = self.env['ir.config_parameter'].sudo().get_param('farmaku.settlement.batch.commission_product_id')
        service_fee_product_id = self.env['ir.config_parameter'].sudo().get_param('farmaku.settlement.batch.service_fee_product_id')
        sequence_format = self.env['ir.config_parameter'].sudo().get_param('farmaku.settlement.batch.sequence_format')

        res.update(
            gross_amount_product_id=int(gross_amount_product_id or 0),
            subsidy_amount_product_id=int(subsidy_amount_product_id or 0),
            shipping_cost_product_id=int(shipping_cost_product_id or 0),
            voucher_amount_product_id=int(voucher_amount_product_id or 0),
            commission_product_id=int(commission_product_id or 0),
            service_fee_product_id=int(service_fee_product_id or 0),
            sequence_format=sequence_format or '',
        )

        return res
