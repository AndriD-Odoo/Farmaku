# -*- coding: utf-8 -*-
import io
import xlsxwriter
import werkzeug

from odoo import http
from odoo.addons.web.controllers.main import serialize_exception, content_disposition


class StockExtended(http.Controller):

    @http.route(['/reordering_rule/export_excel'],
                type='http', auth="public", methods=['GET'])
    def export_to_excel(self, wizard_id):
        wizard_id = http.request.env['orderpoint.report.wizard'].browse(int(wizard_id))
        response = http.request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition(f'{wizard_id.datas_fname}.xlsx'))
            ]
        )
        fp, filename = wizard_id.get_content()
        fp.seek(0)
        response.stream.write(fp.read())
        fp.close()
        return response
