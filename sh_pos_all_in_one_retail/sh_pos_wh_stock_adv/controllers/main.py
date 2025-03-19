# Copyright (C) Softhealer Technologies.

from odoo.http import request
from odoo import  http
from odoo.addons.bus.controllers.main import BusController


class UpdateRealTimeQuantity(http.Controller):
    @http.route('/update_quanttiy', type='http', auth="public", methods=['GET'])
    def update_real_time_quantity(self, **post):
        passed_data = {}
        if post:
            if post.get('passed_list[product_id][]') and post.get('passed_list[location_id][]') and post.get('passed_list[quantity]'):
                product_obj = request.env['product.product'].search(
                    [('id', '=', post.get('passed_list[product_id][]'))])
                if product_obj:
                    passed_data['product_id'] = [
                        product_obj.id, product_obj.name]

                location_obj = request.env['stock.location'].search(
                    [('id', '=', post.get('passed_list[location_id][]'))])
                if location_obj:
                    passed_data['location_id'] = [
                        location_obj.id, location_obj.name]

                passed_data['quantity'] = post.get('passed_list[quantity]')

        pos_session = request.env['pos.session'].search(
            [('state', 'in', ['opened', 'opening_control'])])
        if pos_session and passed_data:
            for each_session in pos_session:
                if each_session.config_id and each_session.config_id.sh_update_quantity_cart_change:
                    request.env['bus.bus'].sendmany(
                        [[(request._cr.dbname, 'stock.update', each_session.user_id.id), {'stock_update': [passed_data]}]])
                else:
                    if post.get('passed_list[is_valid_order]'):
                        request.env['bus.bus'].sendmany(
                            [[(request._cr.dbname, 'stock.update', each_session.user_id.id), {'stock_update': [passed_data]}]])
        return []


class PosOrderController(BusController):

    def _poll(self, dbname, channels, last, options):
        """Add the relevant channels to the BusController polling."""
        if options.get('stock.update'):
            channels = list(channels)
            lock_channel = (
                request.db,
                'stock.update',
                options.get('stock.update')
            )
            channels.append(lock_channel)
        return super(PosOrderController, self)._poll(dbname, channels, last, options)