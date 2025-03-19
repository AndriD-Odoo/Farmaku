import logging
import json
import functools

from datetime import datetime
from odoo import http, SUPERUSER_ID
from odoo.tools import config
from werkzeug.wrappers import Request, Response
from passlib.context import CryptContext

crypt_context = CryptContext(schemes=['pbkdf2_sha512', 'plaintext'],
                             deprecated=['plaintext'])
_logger = logging.getLogger(__name__)

HEADERS = {'Content-Type': 'application/json'}


def success_response(status_code, result):
    if http.request._request_type == 'http':
        data = {
            'jsonrpc': '2.0',
            'id': http.request.httprequest.headers.get('id', 0),
            'result': result,
        }
        response = Response(json.dumps(data), status=status_code, headers=HEADERS)
    else:
        response = {
            'rest_api_status_code': status_code,
            'result': result,
        }
    return response


def error_response(status_code, error_message, error_type='general'):
    if not error_type:
        error_type = 'general'
    if http.request._request_type == 'http':
        data = {
            'jsonrpc': '2.0',
            'id': http.request.httprequest.headers.get('id', 0),
            'result': {
                'error_type': error_type,
                'error_message': error_message,
            }
        }
        response = Response(json.dumps(data), status=status_code, headers=HEADERS)
    else:
        result = {
            'error_type': error_type,
            'error_message': error_message,
        }
        response = {
            'rest_api_status_code': status_code,
            'result': result,
        }
    return response


def authentication(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        _logger.info(f'\nfunc: {func}')
        _logger.info(f'\nargs: {args}')
        _logger.info(f'\nkwargs: {kwargs}')
        uid = False
        try:
            api_key = http.request.httprequest.headers.get('X-Api-Key')
            _logger.info(f'\napi_key: {api_key}')
            uid = http.request.env['res.users.apikeys'].sudo()._check_credentials(scope='rpc', key=api_key)
        except Exception as e:
            _logger.info(f'error: {str(e)}')
        if not uid:
            return error_response(status_code=403, error_type='access_denied', error_message='Invalid API Key')
        # dijalankan sebagai user public
        public_user_id = http.request.env.ref('base.public_user')
        http.request.uid = public_user_id.id
        return func(self, *args, **kwargs)
    return wrap


def check_mandatory_fields(mandatory_fields, val):
    need_fields = []
    for mandatory_field in mandatory_fields:
        if not val.get(mandatory_field):
            need_fields.append(mandatory_field)
    return need_fields
