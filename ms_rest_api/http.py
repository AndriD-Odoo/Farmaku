import json

from odoo import http
from odoo.tools import date_utils
from werkzeug.wrappers import Response


class JsonRequestExtended(http.JsonRequest):

    def _json_response(self, result=None, error=None):
        id = self.jsonrequest.get('id')
        if not id and http.request.httprequest.headers.get('id', 0):
            id = http.request.httprequest.headers.get('id', 0)
        status = error and error.pop('http_status', 200) or 200
        if isinstance(result, dict):
            if result.get('rest_api_status_code'):
                status = result['rest_api_status_code']
                result = result['result']
        response = {
            'jsonrpc': '2.0',
            'id': id
        }
        if error is not None:
            response['error'] = error
        if result is not None:
            response['result'] = result

        mime = 'application/json'
        body = json.dumps(response, default=date_utils.json_default)

        return Response(
            body, status=status,
            headers=[('Content-Type', mime), ('Content-Length', len(body))]
        )


http.JsonRequest._json_response = JsonRequestExtended._json_response
