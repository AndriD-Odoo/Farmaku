import json

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo import http, SUPERUSER_ID
from werkzeug.wrappers import Request, Response

from odoo.addons.ms_rest_api.models.common import (
    _logger,
    success_response,
    error_response,
    authentication,
    check_mandatory_fields
)


class Users(http.Controller):

    @http.route(
        '/api/users',
        type='http', auth="none", methods=['GET'], csrf=False)
    @authentication
    def get_users(self, **kwargs):
        _logger.info(f'\n{kwargs}')
        error_detail = {}
        data = []
        try:
            criteria = []
            if kwargs.get('login'):
                criteria += [
                    ('login', '=', kwargs['login'])
                ]
            user_ids = http.request.env['res.users'].sudo().search(criteria)
            for user_id in user_ids:
                data.append({
                    'name': user_id.name,
                    'login': user_id.login,
                    'mobile': user_id.mobile or '',
                    'email': user_id.email or '',
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
                status_code=200,
                result=data
            )

    @http.route(
        '/api/user/<id>',
        type='http', auth="none", methods=['GET'], csrf=False)
    @authentication
    def get_user(self, id):
        _logger.info(f'\n{id}')
        error_detail = {}
        data = {}
        try:
            criteria = [('id', '=', int(id))]
            user_id = http.request.env['res.users'].sudo().search(criteria)
            if not user_id:
                error_detail.update({
                    'status_code': 404,
                    'error_type': 'data_not_found',
                    'error_message': f'User ID {id} not found.',
                })
            else:
                data = {
                    'name': user_id.name,
                    'login': user_id.login,
                    'mobile': user_id.mobile or '',
                    'email': user_id.email or '',
                }
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
                status_code=200,
                result=data
            )

    @http.route(
        '/api/user',
        type='json', auth="none", methods=['POST'], csrf=False)
    @authentication
    def create_user(self):
        vals = http.request.jsonrequest
        _logger.info(f'\n{vals}')
        error_detail = {}
        data = {}
        try:
            mandatory_fields = [
                'name',
                'login',
            ]
            need_fields = check_mandatory_fields(mandatory_fields=mandatory_fields, val=vals)
            if need_fields:
                error_detail.update({
                    'status_code': 400,
                    'error_type': 'mandatory_fields',
                    'error_message': ', '.join(need_fields),
                })
            else:
                user_id = http.request.env['res.users'].sudo().create({
                    'name': vals['name'],
                    'login': vals['login'],
                    'mobile': vals.get('mobile'),
                    'email': vals.get('email'),
                })
                data.update({
                    'user_id': user_id.id,
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

    @http.route(
        '/api/user/<id>',
        type='json', auth="none", methods=['PUT'], csrf=False)
    @authentication
    def edit_user(self, id):
        body = http.request.jsonrequest
        _logger.info(f'\n{id}')
        error_detail = {}
        data = {}
        try:
            criteria = [('id', '=', int(id))]
            user_id = http.request.env['res.users'].sudo().search(criteria)
            if not user_id:
                error_detail.update({
                    'status_code': 404,
                    'error_type': 'data_not_found',
                    'error_message': f'User ID {id} not found.',
                })
            else:
                vals = {}
                if 'name' in body:
                    vals['name'] = body['name']
                if 'login' in body:
                    vals['login'] = body['login']
                if 'mobile' in body:
                    vals['mobile'] = body['mobile']
                if 'email' in body:
                    vals['email'] = body['email']
                user_id.write(vals)
                data.update({
                    'user_id': user_id.id,
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
                status_code=200,
                result=data
            )

    @http.route(
        '/api/user/<id>',
        type='http', auth="none", methods=['DELETE'], csrf=False)
    @authentication
    def delete_user(self, id):
        _logger.info(f'\n{id}')
        error_detail = {}
        data = {}
        try:
            criteria = [('id', '=', int(id))]
            user_id = http.request.env['res.users'].sudo().search(criteria)
            if not user_id:
                error_detail.update({
                    'status_code': 404,
                    'error_type': 'data_not_found',
                    'error_message': f'User ID {id} not found.',
                })
            else:
                data = {
                    'user_id': user_id.id
                }
                user_id.unlink()
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
                status_code=200,
                result=data
            )
