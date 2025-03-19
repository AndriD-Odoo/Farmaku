# -*- coding: utf-8 -*-
from odoo import http, modules
from odoo.http import request, route

from odoo.addons.ms_rest_api.models.common import (
    _logger,
    success_response,
    error_response,
    authentication,
    check_mandatory_fields
)


class HrExtended(http.Controller):
    @route('/api/v1/attendance', methods=['POST'], type='json', auth='public', csrf=False)
    @authentication
    def send_attendance(self):
        vals = http.request.jsonrequest.get('attendances', [])
        _logger.info(f'\n{vals}')
        error_detail = {}
        data = {}
        try:
            need_fields = []
            for val in vals:
                mandatory_fields = [
                    'reference_id',
                    'barcode',
                    'check_in',
                    'check_out',
                ]
                need_fields = check_mandatory_fields(
                    mandatory_fields=mandatory_fields,
                    val=val
                )
            if need_fields:
                error_detail.update({
                    'status_code': 400,
                    'error_type': 'mandatory_fields',
                    'error_message': ', '.join(need_fields),
                })
            else:
                result = request.env['hr.attendance'].sudo().create_attendance(vals=vals)
                if result.get('code') != 200:
                    error_detail.update({
                        'status_code': result.get('code', 400),
                        'error_type': 'general',
                        'error_message': result.get('message'),
                    })
                else:
                    data.update({
                        "message": result.get('message'),
                        "record_ids": result.get('record_ids'),
                        "failed_detail": result.get('failed_detail'),
                    })
        except Exception as e:
            error_detail.update({
                'status_code': 500,
                'error_type': 'general',
                'error_message': str(e),
            })
        if error_detail:
            return error_response(
                status_code=error_detail['status_code'],
                error_message=error_detail['error_message'],
                error_type=error_detail.get('error_type')
            )
        else:
            return success_response(
                status_code=201,
                result=data
            )
