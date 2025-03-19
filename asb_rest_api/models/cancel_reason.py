from odoo import models, fields, registry, api, _
from odoo.exceptions import UserError, ValidationError
import traceback as tb
import requests
import logging
import base64
import json

_logger = logging.getLogger(__name__)


class CancelReason(models.Model):
    _name = 'cancel.reason'
    _description = 'Cancel Reason'
    _order = 'farmaku_cancel_reason_id'

    farmaku_cancel_reason_id = fields.Integer(string='Cancel Reason ID')
    name = fields.Char(string='Cancel Name')

    def _get_auth(self):
        server_key = self.env['ir.config_parameter'].sudo().get_param('farmaku_server_key')
        auth = base64.b64encode(bytes("{auth}{colon}".format(auth=server_key, colon=":"), 'utf-8')).decode('UTF-8')
        return auth
    
    def _get_url(self, parameter):
        url = self.env['ir.config_parameter'].sudo().get_param('farmaku_url')
        url_odoo = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if url == 'https://pharmacy-api.securerx.id' and url_odoo != 'https://farmaku.odoo.com':
            raise ValidationError(_('Url API Production Farmaku can use in Url Production Odoo'))
        endpoint = '/'.join([url,self.env['ir.config_parameter'].sudo().get_param('farmaku_{param}_endpoint'.format(param=parameter))])
        return endpoint
    
    def create_cancel_reason(self, data):
        self.create({
            'farmaku_cancel_reason_id': data['id'],
            'name': data['name']
        })

    def write_cancel_reason(self, cancel_reason_id, data):
        cancel_reason_id.write({
            'farmaku_cancel_reason_id': data['id'],
            'name': data['name']
        })

    def sync_get_cancel_reason(self):
        parameter = "order_cancelreason"
        auth = self._get_auth()
        url = self._get_url(parameter)
        headers = {
            "Authorization": "Basic {auth}".format(auth=auth),
            "Content-Type": "application/json"
        }
        body = {}
        try:
            r = requests.get(url=url, headers=headers)
            _logger.info('# Request Obtaining Get Cancel Reason #')
            if r.status_code == 200:
                _logger.info('# Request Obtaining Get Cancel Reason Success #')
                _logger.info(r.text)
                for data in r.json():
                    cancel_reason_id = self.sudo().search([
                        ('farmaku_cancel_reason_id', '=', data['id'])
                    ])
                    if not cancel_reason_id:
                        self.create_cancel_reason(data)
                    else:
                        self.write_cancel_reason(cancel_reason_id, data)
                self.env.user.create_connector_log(
                    url=url,
                    method='GET',
                    headers=headers,
                    body=body,
                    response=r,
                    response_body=False,
                )
            else:
                _logger.warning('# Request Obtaining Get Cancel Reason Failed, code {code} #'.format(code=r.status_code))
                _logger.warning(r.text)
                return {}
        except Exception as e:
            _logger.error('# Request Obtaining Get Cancel Reason Failed, code {code} #'.format(code=r.status_code))
            _logger.error(e.args[0])
            return False

    def get_cancel_reason_by_id(self, farmaku_cancel_reason_id):
        cancel_reason_id = self.search([
            ('farmaku_cancel_reason_id', '=', farmaku_cancel_reason_id)
        ], limit=1)
        return cancel_reason_id
