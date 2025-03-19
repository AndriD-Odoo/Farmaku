# from odoo import http, _
# from odoo.http import request, route
# from odoo.tools.config import config
#
# import werkzeug
# import json
# import functools
# import base64
#
# def _response(headers, body, status=200, request_type='http'):
#     if request_type == 'json':
#         response = {}
#         response['error'] =[{
#                     'code': status,
#                     'message': body['message'],
#             }]
#         response['route'] = True
#         return response
#     try:
#         fixed_headers = {str(k): v for k, v in headers.items()}
#     except:
#         fixed_headers = headers
#     response = werkzeug.Response(response=json.dumps(body), status=status, headers=fixed_headers)
#     return response
#
# def auth_required(**kw):
#     def decorator(f):
#         @functools.wraps(f)
#         def wrapper(*args, **kw):
#             headers = dict(request.httprequest.headers.items())
#             request_type = request._request_type
#             auth = headers.get('Authorization', None)
#             #Ref https://github.com/mgonto/auth0-python-flaskapi-sample/blob/master/server.py
#             if not auth:
#                 return {'error' : {'code': 403, 'message': 'No Authorization'}}
#             parts = auth.split()
#             if parts[0].lower() != 'basic':
#                 return {'error' : {'code': 403, 'message': 'Authorization header must start with Basic'}}
#             elif len(parts) == 1:
#                 return {'error' : {'code': 403, 'message': 'Basic auth not found'}}
#             elif len(parts) > 2:
#                 return {'error' : {'code': 403, 'message': 'Authorization header must be Basic + \s + Encrypted Key'}}
#             key = parts[1]
#             encrypted_key = base64.b64decode(bytes("{auth}{colon}".format(auth=key, colon=":"), 'utf-8')).decode('UTF-8').rstrip(":")
#             if encrypted_key != request.env['ir.config_parameter'].sudo().get_param('farmaku_client_key'):
#                 return {'error' : {'code': 401, 'message': 'Client Key is invalid'}}
#             response = f(*args, **kw)
#             return response
#         return wrapper
#     return decorator
