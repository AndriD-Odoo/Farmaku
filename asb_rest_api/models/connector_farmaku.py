from odoo import models, fields, registry, api, _
import logging

_logger = logging.getLogger(__name__)


class ConnectorFarmaku(models.Model):
    _name = 'connector.farmaku'
    _description = 'Connector Farmaku'
    _order = 'request_time DESC'
    _rec_name = 'url'

    def _filename(self):
        for log in self:
            log.is_request_body = bool(log.request_body)
            log.header_filename = 'header.json'
            log.request_filename = log.is_request_body and 'request.json'
            log.response_filename = 'response.json' if log.status_code == '200' else 'error.log'

    url = fields.Char(string='URL')
    request_method = fields.Char(string='Request Method')
    request_time = fields.Datetime(string='Request Time', index=True)
    response_time = fields.Datetime(string='Response Time')
    request_header = fields.Binary(string='Request Header')
    request_body = fields.Binary(string='Request Body')
    response_body = fields.Binary(string='Response Body')
    is_request_body = fields.Boolean(compute='_filename')
    status_code = fields.Char(string='Status Code')
    header_filename = fields.Char('Header File Name', compute="_filename")
    request_filename = fields.Char('Request File Name', compute="_filename")
    response_filename = fields.Char('Response File Name', compute="_filename")

    def action_download_request(self):
        return {
            'type': 'ir.actions.act_url',
            'name': 'Request Body',
            'url': '/web/content/connector.farmaku/%s/request_body/%s?download=true' % (self.ids[0], self.request_filename),
        }

    def action_download_response(self):
        return {
            'type': 'ir.actions.act_url',
            'name': 'Response Body',
            'url': '/web/content/connector.farmaku/%s/response_body/%s?download=true' % (self.ids[0], self.response_filename),
        }

    def action_download_header(self):
        return {
            'type': 'ir.actions.act_url',
            'name': 'Request Header',
            'url': '/web/content/connector.farmaku/%s/request_header/%s?download=true' % (self.ids[0], self.header_filename),
        }
