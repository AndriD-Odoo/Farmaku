from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime

import base64
import json
import requests
import dateutil.parser

import logging
_logger = logging.getLogger(__name__)


class LogImportDataPharmacyProduct(models.Model):
    _name = 'log.import.pharmacyproduct'
    _description = 'Log Import Pharmacy Product'

    name = fields.Char(string='Original File Name')
    farmaku_log_id = fields.Integer(string="id")
    index_name = fields.Char(string='Index Name')
    total_row = fields.Integer(string='Total Row')
    indexed_record = fields.Integer(string='Indexed Record')
    ignored_row = fields.Integer(string='Ignored Row')
    failed_record = fields.Integer(string='Failed Record')
    progress = fields.Integer(string='Progress')
    duration = fields.Integer(string='Duration')
    remark = fields.Char(string='Remark')
    status = fields.Char(string='Status')
    date = fields.Datetime(string='Date')
    initiated_by = fields.Char(string='Initiated By')

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

    def _sync_get_logs_import_data(self, data):
        parameter = "logs_importdata"
        auth = self._get_auth()
        url = self._get_url(parameter)
        headers = {
            "Authorization": "Basic {auth}".format(auth=auth),
            "Content-Type": "application/json"
        }
        body = {}

        if data:
            url += '/'+ str(data['logId'])

        try:
            r = requests.get(url=url, headers=headers)
            _logger.info('# Request Obtaining Get Log Import Data #')
            if r.status_code == 200:
                _logger.info('# Request Obtaining Get Log Import Data Success #')
                _logger.info(r.text)
                self.env.user.create_connector_log(
                    url=url,
                    method='GET',
                    headers=headers,
                    body=body,
                    response=r,
                    response_body=False,
                )
                r_data = r.json()
                self.create({
                    'name': r_data['originalFilename'],
                    'farmaku_log_id': r_data['id'],
                    'index_name': r_data['indexName'],
                    'total_row': r_data['totalRow'],
                    'indexed_record': r_data['indexedRecord'],
                    'ignored_row': r_data['ignoredRow'],
                    'failed_record': r_data['failedRecord'],
                    'progress': r_data['progress'],
                    'duration': r_data['duration'],
                    'remark': r_data['remark'],
                    'status': r_data['status'],
                    'date': dateutil.parser.isoparse(r_data['date']).replace(tzinfo=None),
                    'initiated_by': r_data['initiatedBy']
                })
            else:
                _logger.warning('# Request Obtaining Get Log Import Data Failed, code {code} #'.format(code=r.status_code))
                _logger.warning(r.text)
                return {}
        except Exception as e:
            _logger.error('# Request Obtaining Get Log Import Data Failed, code {code} #'.format(code=r.status_code))
            _logger.error(e.args[0])
            return False