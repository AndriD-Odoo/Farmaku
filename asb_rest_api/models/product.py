import base64
import json
import requests
import requests_toolbelt

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        # res = super(ProductTemplate, self).write(vals)
        for product in self:
            if vals.get('list_price', product.list_price) != product.list_price:
                product_id = self.env['product.product'].search(['|',('default_code','=',product.default_code),('barcode','=',product.barcode)])
                pharmacy_code_ids = self.env['stock.warehouse'].search([]).filtered(lambda r: r.pharmacy_code).mapped('pharmacy_code')
                for pharmacy_code in pharmacy_code_ids:
                    product_id._sync_update_price(product_id, vals.get('list_price'), pharmacy_code)
        return super(ProductTemplate, self).write(vals)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_mapped = fields.Boolean(string='Mapped ?')

    def api_get_product(self, product_id=False, **kwargs):
        # uid = kwargs.get('uid',1)
        if product_id:
            product_ids = self.env['product.product'].sudo().search([
                ('id', '=', product_id),
            ])
        else:
            product_ids = self.env['product.product'].sudo().search([])
        result = [{
            'productName': l.name,
            'price': l.list_price,
            'normalPrice': l.normal_price,
            'brandId': l.brand_id,
            'uomId': l.uom_id,
            'isActive': l.active,
            'isDeleted': l.is_deleted,
            'createUid': l.create_uid,
            'createDate': l.create_date,
            'modifiedDate': l.write_date,
            'modifiedUid': l.write_uid,
            'dbNote': l.db_note,
            'productDotColorId': l.product_dot_color_id,
            'productTypeId': l.product_type_id,
            'barcode': l.barcode,
            'productCode': l.default_code,
            'forconcoction': l.forconcoction,
            'forprescription': l.forprescription,
            'attention': l.attention,
            'contraindication': l.contraindication,
            'description': l.description,
            'dimensionLength': l.dimension_length,
            'dimensionWeight': l.weight,
            'dimensionWidth': l.dimension_width,
            'dimensionHeight': l.dimension_height,
            'dosage': l.dosage,
            'drugInteraction': l.drug_interaction,
            'howToUse': l.how_to_use,
            'indication': l.indication,
            'isBackorder': l.is_backorder,
            'isFulfilledBymitra': l.is_fullfilled_bymitra,
            'longDescription': l.long_description,
            'minStock': l.min_stock,
            'principalId': l.principal_id,
            'sideEffect': l.side_effect,
            'conversion': l.conversion,
            'conversionOperator': l.conversion_operator,
            'isBestSelling': l.is_best_selling,
            'isNewArrival': l.is_new_arrival,
            'isTopOffer': l.is_top_offer,
            'productKey': l.product_key,
            'metaKeyword': l.meta_keyword,
            'metaDescription': l.meta_description
        } for l in product_ids]
        return {'code': 200, 'total_record': len(result), 'data': result}

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

    def _sync_get_products(self, data):
        parameter = "pharmacies_product"
        auth = self._get_auth()
        url = self._get_url(parameter)
        headers = {
            "Authorization": "Basic {auth}".format(auth=auth),
            "Content-Type": "application/json"
        }
        body = {}

        if data['page'] and data['item_per_page']:
            url += "?Page=" + str(data['page']) + "&ItemsPerPage=" + str(data['item_per_page']) + "&"
        elif data['page']:
            url += "?Page=" + str(data['page']) + "&"
        elif data['item_per_page']:
            url += "?ItemsPerPage=" + str(data['item_per_page']) + "&"
        else:
            url += "?"
        
        if data['search_product']:
            url += "Search=" + str(data['search_product']) + "&"

        if data['product_ids'] and data['pharmacy_code']:
            product_list = []
            for product in data['product_ids']:
                product_list.append(product.default_code)
            url += "productCodes=" + str(product_list) + "&pharmacyCode=" + str(data['pharmacy_code'])
        elif data['product_ids']:
            product_list = []
            for product in data['product_ids']:
                product_list.append(product.default_code)
            url += "productCodes=" + str(product_list)
        elif data['pharmacy_code']:
            url += "pharmacyCode=" + str(data['pharmacy_code'])
        else:
            url = url[:-1]

        try:
            r = requests.get(url=url, headers=headers)
            _logger.info('# Request Obtaining Get Pharmacies Product #')
            self.env.user.create_connector_log(
                url=url,
                method='GET',
                headers=headers,
                body=body,
                response=r,
                response_body=False,
            )
            if r.status_code == 200:
                _logger.info('# Request Obtaining Get Pharmacies Product Success #')
                _logger.info(r.text)

                url2 = self._get_url(parameter)
                if data['page'] and data['item_per_page']:
                    url2 += "?Page=" + str(data['page']) + "&ItemsPerPage=" + str(r.json().get('totalRecords', 0)) + "&"
                elif data['page']:
                    url2 += "?Page=" + str(data['page']) + "&"
                elif data['item_per_page']:
                    url2 += "?ItemsPerPage=" + str(r.json().get('totalRecords', 0)) + "&"
                else:
                    url2 += "?"
                
                if data['search_product']:
                    url2 += "Search=" + str(data['search_product']) + "&"

                if data['product_ids'] and data['pharmacy_code']:
                    product_list = []
                    for product in data['product_ids']:
                        product_list.append(product.default_code)
                    url2 += "productCodes=" + str(product_list) + "&pharmacyCode=" + str(data['pharmacy_code'])
                elif data['product_ids']:
                    product_list = []
                    for product in data['product_ids']:
                        product_list.append(product.default_code)
                    url2 += "productCodes=" + str(product_list)
                elif data['pharmacy_code']:
                    url2 += "pharmacyCode=" + str(data['pharmacy_code'])
                else:
                    url2 = url2[:-1]
                r2 = requests.get(url=url2, headers=headers)
                if r2.status_code == 200:
                    _logger.info('# Request Obtaining Get Pharmacies Product #')
                    self.env.user.create_connector_log(
                        url=url,
                        method='GET',
                        headers=headers,
                        body=body,
                        response=r,
                        response_body=False,
                    )
                    return r2.json()
                else:
                    _logger.warning('# Request Obtaining Get Pharmacies Product 2 Success with Error #')
                    _logger.warning(r.text)
            else:
                _logger.warning('# Request Obtaining Get Pharmacies Product 1 Success with Error #')
                _logger.warning(r.text)
        except Exception as e:
            _logger.error('# Request Obtaining Get Pharmacies Product Failed #')
            _logger.error(e.args[0])
            return False

    def get_available_qty(self, pharmacy_code):
        self.ensure_one()
        warehouse_id = self.env['stock.warehouse'].search([('pharmacy_code', '=', pharmacy_code)], limit=1)
        if not warehouse_id:
            raise ValidationError(_(f'No warehouse for pharmacy code {pharmacy_code}.'))
        quant_ids = self.env['stock.quant'].sudo().search([
            ('product_id','=', self.id),
            ('location_id.usage','=','internal'),
            ('location_id','child_of', warehouse_id.lot_stock_id.ids)])
        warehouse_quantity = sum(quant_ids.mapped('available_quantity'))
        if warehouse_quantity < 0 :
            warehouse_quantity = 0
        return warehouse_quantity

    def _sync_update_stock(self, pharmacy_code):
        if not pharmacy_code:
            return False
        parameter = "pharmacies_product_stock"
        auth = self._get_auth()
        headers = {
            "Authorization": "Basic {auth}".format(auth=auth),
            "Content-Type": "application/json"
        }
        body = []
        url = self._get_url(parameter)
        url += "?pharmacyCode=" + str(pharmacy_code)
        for product in self:
            qty = product.get_available_qty(pharmacy_code)
            product_dict = {
                "productCode": product.default_code or product.barcode,
                "stock": int(qty)
            }
            self.env['sync.stock.log'].create({
                'warehouse_code': pharmacy_code,
                'product_code': product.default_code or product.barcode,
                'action': self.env.context.get('action'),
                'qty': int(qty),
                'name': self.env.context,
            })
            body.append(product_dict)
        _logger.info(f'\n body sync stock {pharmacy_code} {body}')
        r = requests.put(url=url, headers=headers, json=body)
        if r.status_code == 404:
            raise ValidationError(_('# Request Update Stock Failed, code {code} #'.format(code=r.status_code)))
        try:
            self.env.user.create_connector_log(
                url=url,
                method='PUT',
                headers=headers,
                body=body,
                response=r,
                response_body=False,
            )
            _logger.info('# Request Update Stock #')
            if r.status_code == 200:
                _logger.info('# Request Update Stock Success #')
                _logger.info(r.text)
            else:
                _logger.warning('# Request Update Stock Failed, code {code} #'.format(code=r.status_code))
                _logger.warning(r.text)
        except Exception as e:
            _logger.error('# Request Update Stock Failed, code {code} #'.format(code=r.status_code))
            _logger.error(e.args[0])

    def _sync_update_price(self, product_ids, sale_price, pharmacy_code=False):
        parameter = "pharmacies_product_price"
        auth = self._get_auth()
        url = self._get_url(parameter)
        headers = {
            "Authorization": "Basic {auth}".format(auth=auth),
            "Content-Type": "application/json"
        }

        body = []
        for product in product_ids:
            product_dict = {
                "productCode": product.default_code or product.barcode,
                "unitPrice": sale_price
            }
            body.append(product_dict)

        if pharmacy_code:
            url += "?pharmacyCode=" + str(pharmacy_code)
        
        try:
            r = requests.put(url=url, headers=headers, json=body)
            _logger.info('# Request Update Price #')
            self.env.user.create_connector_log(
                url=url,
                method='PUT',
                headers=headers,
                body=body,
                response=r,
                response_body=False,
            )
            if r.status_code == 200:
                _logger.info('# Request Update Price Success #')
                _logger.info(r.text)
            else:
                _logger.warning('# Request Update Price Failed, code {code} #'.format(code=r.status_code))
                _logger.warning(r.text)
                # return {}
        except Exception as e:
            _logger.error('# Request Update Price Failed, code {code} #'.format(code=r.status_code))
            _logger.error(e.args[0])
            # return False
    
    def _sync_upload_products(self, data):
        parameter = "pharmacies_product_upload"
        auth = self._get_auth()
        url = self._get_url(parameter)
        files = {'file': (data['filename'], base64.b64decode(data['file']).decode(), 'text/csv')}
        headers = {
            "Authorization": "Basic {auth}".format(auth=auth),
        }

        url += "?Format=" + str(data['csv_format']) + "&Delimiter=" + str(data['delimiter']) + "&RowStart=" + str(data['row_start'])
        if data['worksheet_name']:
            url += "&WorksheetName=" + str(data['worksheet_name'])

        try:
            requests.packages.urllib3.disable_warnings()
            r = requests.post(url=url, headers=headers, files=files, verify=False)
            _logger.info('# Request Upload Product #')
            self.env.user.create_connector_log(
                url=url,
                method='POST',
                headers=headers,
                body=body,
                response=r,
                response_body=False,
            )
            if r.status_code == 200:
                _logger.info('# Request Upload Product Success #')
                _logger.info(r.text)
                r_data = r.json()
                self.env['log.import.pharmacyproduct']._sync_get_logs_import_data(r_data)
            else:
                _logger.warning('# Request Upload Product Failed, code {code} #'.format(code=r.status_code))
                _logger.warning(r.text)
        except Exception as e:
            _logger.error('# Request Upload Product Failed, code {code} #'.format(code=r.status_code))
            _logger.error(e.args[0])    
    