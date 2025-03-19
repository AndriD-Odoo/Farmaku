from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import pytz
import requests


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_yesterday(self):
        return pytz.UTC.localize(fields.Datetime.now()).astimezone(pytz.timezone(self.env.user.tz or 'Asia/Jakarta'))\
               - timedelta(days=1)

    def _send_sale_data(self, trx_date=''):
        if not trx_date:
            trx_date = self.get_yesterday().strftime("%Y-%m-%d")
        start_date = datetime.strptime(trx_date, "%Y-%m-%d") - timedelta(days=1)
        start_date = start_date.strftime("%Y-%m-%d 17:00:00")
        end_date = trx_date + " 17:00:00"
        query = f"""
            SELECT
                DISTINCT(product_id)
            FROM (
                SELECT
                    DISTINCT(sol.product_id)
                FROM
                    sale_order_line sol
                LEFT JOIN
                    sale_order so ON so.id = sol.order_id
                LEFT JOIN
                    product_product pp ON pp.id = sol.product_id
                WHERE
                    so.state IN ('sale', 'done')
                    AND pp.default_code IS NOT NULL
                    AND so.date_order > '{start_date}'
                    AND so.date_order <= '{end_date}'

                UNION ALL

                SELECT
                    DISTINCT(pol.product_id)
                FROM
                    pos_order_line pol
                LEFT JOIN
                    pos_order po ON po.id = pol.order_id
                LEFT JOIN
                    product_product pp ON pp.id = pol.product_id
                WHERE
                    po.state IN ('paid', 'done', 'invoiced')
                    AND pp.default_code IS NOT NULL
                    AND po.date_order > '{start_date}'
                    AND po.date_order <= '{end_date}'
            ) AS sale_data
        """
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()
        product_ids = [0]
        for res in result:
            product_ids.append(res['product_id'])
        product_ids = str(tuple(product_ids)).replace(',)', ')')
        query = f"""
            SELECT
                productCode,
                SUM(soldQty::INTEGER) AS soldQty
            FROM (
                SELECT
                    pp.default_code AS productCode,
                    SUM(COALESCE(sol.product_uom_qty, 0)::INTEGER) AS soldQty
                FROM
                    sale_order_line sol
                LEFT JOIN
                    sale_order so ON so.id = sol.order_id
                LEFT JOIN
                    product_product pp ON pp.id = sol.product_id
                WHERE
                    so.state IN ('sale', 'done')
                    AND sol.product_id in {product_ids}
                GROUP BY
                    pp.default_code
                    
                UNION ALL
                
                SELECT
                    pp.default_code AS productCode,
                    SUM(COALESCE(pol.qty, 0))::INTEGER AS soldQty
                FROM
                    pos_order_line pol
                LEFT JOIN
                    pos_order po ON po.id = pol.order_id
                LEFT JOIN
                    product_product pp ON pp.id = pol.product_id
                WHERE
                    po.state IN ('paid', 'done', 'invoiced')
                    AND pol.product_id in {product_ids}
                GROUP BY
                    pp.default_code
            ) AS sale_data
            GROUP BY
                productCode
        """
        self.env.cr.execute(query)
        ori_result = self.env.cr.dictfetchall()
        result = []
        for res in ori_result:
            new_res = {}
            for key, value in res.items():
                if key == 'productcode':
                    new_res['productCode'] = value
                elif key == 'soldqty':
                    new_res['soldQty'] = value
            result.append(new_res)
        if not result:
            raise ValidationError(_(f'No sale and POS data found at {trx_date}.'))
        parameter = "send_sale_data"
        auth = self._get_auth()
        url = self._get_url(parameter)
        headers = {
            "Authorization": "Basic {auth}".format(auth=auth),
            "Content-Type": "application/json"
        }
        body = result
        response = requests.put(url=url, headers=headers, json=body)
        if response.status_code != 200:
            raise ValidationError(_(f'Data: {str(body)}\n\nStatus: {response.status_code}, Detail: {response.text}'))
