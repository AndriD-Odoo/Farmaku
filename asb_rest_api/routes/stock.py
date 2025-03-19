from odoo import http
from odoo.http import request, route
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.ms_rest_api.models.common import (
    _logger,
    success_response,
    error_response,
    authentication,
    check_mandatory_fields
)


class ApiStock(http.Controller):

    @route('/api/v1/sync_stock', methods=['GET'], type='http', auth='public', csrf=False)
    @authentication
    def sync_stock_from_fe(self, **data):
        pharmacy_code = data.get('pharmacyCode')
        product_code = data.get('productCode')
        warehouse_id = request.env['stock.warehouse'].sudo().search([
            ('pharmacy_code', '=', pharmacy_code),
        ])
        if not warehouse_id:
            return error_response(
                status_code=404,
                error_message='data_not_found',
                error_type=f"pharmacyCode {pharmacy_code} not found."
            )
        product_id = request.env['product.product'].sudo().search([
            '|',
            ('default_code', '=', product_code),
            ('barcode', '=', product_code),
        ])
        if not product_id:
            return error_response(
                status_code=404,
                error_message='data_not_found',
                error_type=f"productCode {product_code} not found."
            )
        try:
            product_id.with_context({'request_fe': True})._sync_update_stock(pharmacy_code=pharmacy_code)
            return success_response(
                status_code=200,
                result={}
            )
        except Exception as e:
            return error_response(
                status_code=500,
                error_message=str(e),
                error_type='general'
            )
