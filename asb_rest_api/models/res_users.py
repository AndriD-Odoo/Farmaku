import base64
import json

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    def create_connector_log(self, url, method, headers, body, response=False, response_body=False):
        if not response_body:
            try:
                if response != False:  # kalau pakai if response hasilnya False
                    response_body = base64.b64encode(json.dumps(response.json()).encode())
            except Exception:
                response_body = False
        self.env['connector.farmaku'].sudo().create({
            'url': url,
            'request_method': method,
            'request_body': base64.b64encode(json.dumps(body).encode()) if body else False,
            'request_time': fields.Datetime.now(),
            'request_header': base64.b64encode(json.dumps(headers).encode()) if headers else False,
            'response_time': fields.Datetime.now(),
            'status_code': response.status_code if response != False else 0,
            'response_body': response_body,
        })
