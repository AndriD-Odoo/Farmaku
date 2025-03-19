# Copyright (C) Softhealer Technologies.
from odoo import fields, models, api
from datetime import datetime, timedelta


class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_allow_return = fields.Boolean(string="Allow Return Order")
    sh_return_more_qty = fields.Boolean(
        string="Allow Return More Than Purchase Item")
    sh_return_print_receipt = fields.Boolean(
        string="Print Information In Receipt")
    sh_allow_exchange = fields.Boolean(string="Allow Exchange Order")
    sh_exchange_print_receipt = fields.Boolean(
        string="Print Exchange Information In Receipt")

    @api.onchange('sh_allow_return', 'sh_allow_exchange')
    def onchangesh_allow_exchange(self):
        if not self.sh_enable_order_list:
            self.sh_enable_order_list = True


class ProductProduct(models.Model):
    _inherit = "product.product"

    sh_product_non_returnable = fields.Boolean(string="Non Returnable")
    sh_product_non_exchangeable = fields.Boolean(string="Non Exchangeable")


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    sh_return_qty = fields.Float(string="Return Qty.")
    sh_exchange_qty = fields.Float(string="Exchange Qty.")


class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_return_order = fields.Boolean(string="Is Return Order?")
    is_exchange_order = fields.Boolean(string="Is Exchange Order?")
    old_pos_reference = fields.Char(string="Return Order")
    return_status = fields.Selection([
        ('nothing_return', 'Nothing Returned'),
        ('partialy_return', 'Partialy Returned'),
        ('fully_return', 'Fully Returned')
    ], string="Return Status", default='nothing_return',
        readonly=True, copy=False, help="Return status of Order")
    total_return_order = fields.Integer(
        compute='_return_order_total', string="Total Return Order",)
    total_exchange_order = fields.Integer(
        compute='_exchange_order_total', string="Total Exchange Order",)
#
    @api.model
    def order_by_id(self,order_ids):
        order_line = []
        order_line_data = []
        order_data = []
        if order_ids and len(order_ids) > 0:
            order_data = self.search_read([('id','in',order_ids)])
            if order_data and len(order_data):
                for each_order_data in order_data:
                    if each_order_data.get('lines'):
                        for each_line in each_order_data.get('lines'):
                            order_line.append(each_line)
        if order_line and len(order_line) > 0:
            order_line_data = self.env['pos.order.line'].search_read([('id','in',order_line)])
        
        return {'order_line_data':order_line_data,'order_data':order_data}
    @api.model
    def sh_get_all_order(self,user_id):
        order_line_by_id = {}
        order_by_id = {}
        non_return_order = []
        return_order = []
        order_data = []
        order_data = self.search_read([('user_id','=',user_id)])
        if order_data and len(order_data) > 0:
            for each_order in order_data:
                if each_order.get('is_return_order') or each_order.get('is_exchange_order'):
                    return_order.append(each_order)
                elif not each_order.get('is_return_order') and not each_order.get('is_exchange_order'):
                    non_return_order.append(each_order)
                order_by_id[each_order.get('id')] = each_order
                if each_order.get('lines'):
                    for each_line in each_order.get('lines'):
                        order_line_obj = self.env['pos.order.line'].search([('id','=',each_line)])
                        if order_line_obj:
                            order_line_by_id[order_line_obj.id] = order_line_obj.read()[0]
        return {'order_line_by_id':order_line_by_id,'order_by_id':order_by_id,'non_return_order':non_return_order,'return_order':return_order,'order_data':order_data}

    @api.model
    def search_return_exchange_order(self, config_data, page_number):

        order_data = []
        showFrom = int(
            config_data['sh_how_many_order_per_page']) * (int(page_number) - 1)
        showTo = showFrom + int(config_data['sh_how_many_order_per_page'])

        if config_data['sh_load_order_by']:

            if config_data['sh_load_order_by'] == 'session_wise':

                if config_data['sh_session_wise_option'] == 'current_session':
                    order_data = self.env['pos.order'].search_read(['|', ('user_id', '=', self.env.user.id), ('assigned_config', '=', config_data['id']), (
                        'session_id', '=', config_data['current_session_id'][0]), ('state', '!=', 'cancel'), '|', ('is_return_order', '=', True), ('is_exchange_order', '=', True)], limit=showTo)

                if config_data['sh_session_wise_option'] == 'last_no_session':
                    all_session = self.env['pos.session'].search_read([])
                    for index, obj in enumerate(all_session):
                        if (index+1) != len(all_session):
                            if (all_session[index]['stop_at'] and all_session[index + 1]):
                                if (all_session[index]['stop_at'] < all_session[index + 1]['stop_at']):
                                    temp = all_session[index]
                                    all_session[index] = all_session[index + 1]
                                    all_session[index + 1] = temp
                    session = []
                    for x in range(0, config_data['sh_last_no_session']):
                        if x < len(all_session):
                            session.append(all_session[x]['id'])
                    if session:
                        order_data = self.env['pos.order'].search_read(['|', ('user_id', '=', self.env.user.id), ('assigned_config', '=', config_data['id']), (
                            'session_id', 'in', session), ('state', '!=', 'cancel'), '|', ('is_return_order', '=', True), ('is_exchange_order', '=', True)], limit=showTo)

            if config_data['sh_load_order_by'] == 'all':
                order_data = self.env['pos.order'].search_read(['|', ('user_id', '=', self.env.user.id), ('assigned_config', '=', config_data['id']), (
                    'state', '!=', 'cancel'), '|', ('is_return_order', '=', True), ('is_exchange_order', '=', True)], limit=showTo)

            if config_data['sh_load_order_by'] == 'day_wise':

                if config_data['sh_day_wise_option'] == 'current_day':
                    today_date = datetime.today().strftime('%Y-%m-%d')
                    order_data = self.env['pos.order'].search_read(['|', ('user_id', '=', self.env.user.id), ('assigned_config', '=', config_data['id']), ('date_order', '>=', (
                        today_date + " 00:00:00")), ('date_order', '<=', (today_date + " 24:00:00")), ('state', '!=', 'cancel'), '|', ('is_return_order', '=', True), ('is_exchange_order', '=', True)], limit=showTo)

                if config_data['sh_day_wise_option'] == 'last_no_day':
                    if config_data['sh_last_no_days']:
                        today_date = datetime.today().strftime('%Y-%m-%d')
                        last_date = datetime.today() - \
                            timedelta(days=config_data['sh_last_no_days'])
                        last_date = last_date.strftime('%Y-%m-%d')
                        order_data = self.env['pos.order'].search_read(['|', ('user_id', '=', self.env.user.id), ('assigned_config', '=', config_data['id']), ('date_order', '<=', (
                            today_date + " 24:00:00")), ('date_order', '>', (last_date + " 24:00:00")), ('state', '!=', 'cancel'), '|', ('is_return_order', '=', True), ('is_exchange_order', '=', True)], limit=showTo)
        order_data = order_data[showFrom:showTo]
        order_line = []
        if order_data and len(order_data) > 0:
            order_ids = []
            for each_order in order_data:
                order_ids.append(each_order.get('id'))
            order_line = self.env['pos.order.line'].search_read(
                [('order_id', 'in', order_ids)])
        return {'order': order_data, 'order_line': order_line}

    @api.model
    def search_return_order_length(self, config_data):
        order_data = []
        if config_data['sh_load_order_by']:

            if config_data['sh_load_order_by'] == 'session_wise':

                if config_data['sh_session_wise_option'] == 'current_session':
                    order_data = self.env['pos.order'].search_read([('user_id', '=', self.env.user.id), (
                        'session_id', '=', config_data['current_session_id'][0]), ('state', '!=', 'cancel')])

                if config_data['sh_session_wise_option'] == 'last_no_session':
                    all_session = self.env['pos.session'].search_read([])
                    for index, obj in enumerate(all_session):
                        if (index+1) != len(all_session):
                            if (all_session[index]['stop_at'] and all_session[index + 1]):
                                if (all_session[index]['stop_at'] < all_session[index + 1]['stop_at']):
                                    temp = all_session[index]
                                    all_session[index] = all_session[index + 1]
                                    all_session[index + 1] = temp
                    session = []
                    for x in range(0, config_data['sh_last_no_session']):
                        if x < len(all_session):
                            session.append(all_session[x]['id'])
                    if session:
                        order_data = self.env['pos.order'].search_read(
                            [('user_id', '=', self.env.user.id), ('session_id', 'in', session), ('state', '!=', 'cancel')])

            if config_data['sh_load_order_by'] == 'all':
                order_data = self.env['pos.order'].search_read(
                    [('user_id', '=', self.env.user.id), ('state', '!=', 'cancel')])

            if config_data['sh_load_order_by'] == 'day_wise':

                if config_data['sh_day_wise_option'] == 'current_day':
                    today_date = datetime.today().strftime('%Y-%m-%d')
                    order_data = self.env['pos.order'].search_read([('user_id', '=', self.env.user.id), ('date_order', '>=', (
                        today_date + " 00:00:00")), ('date_order', '<=', (today_date + " 24:00:00")), ('state', '!=', 'cancel')])

                if config_data['sh_day_wise_option'] == 'last_no_day':
                    if config_data['sh_last_no_days']:
                        today_date = datetime.today().strftime('%Y-%m-%d')
                        last_date = datetime.today() - \
                            timedelta(days=config_data['sh_last_no_days'])
                        last_date = last_date.strftime('%Y-%m-%d')
                        order_data = self.env['pos.order'].search_read([('user_id', '=', self.env.user.id), ('date_order', '<=', (
                            today_date + " 24:00:00")), ('date_order', '>', (last_date + " 24:00:00")), ('state', '!=', 'cancel')])
        order_line = []
        if order_data and len(order_data) > 0:
            order_ids = []
            for each_order in order_data:
                order_ids.append(each_order.get('id'))
            order_line = self.env['pos.order.line'].search_read(
                [('order_id', 'in', order_ids)])

        return {'order': order_data, 'order_line': order_line}

    @api.model
    def search_return_order(self, config_data, page_number):
        order_data = []
        showFrom = int(
            config_data['sh_how_many_order_per_page']) * (int(page_number) - 1)
        showTo = showFrom + int(config_data['sh_how_many_order_per_page'])

        if config_data['sh_load_order_by']:

            if config_data['sh_load_order_by'] == 'session_wise':

                if config_data['sh_session_wise_option'] == 'current_session':
                    order_data = self.env['pos.order'].search_read([('user_id', '=', self.env.user.id), ('session_id', '=', config_data['current_session_id'][0]), (
                        'state', '!=', 'cancel'), ('is_return_order', '=', False), ('is_exchange_order', '=', False)], limit=showTo)

                if config_data['sh_session_wise_option'] == 'last_no_session':
                    all_session = self.env['pos.session'].search_read([])
                    for index, obj in enumerate(all_session):
                        if (index+1) != len(all_session):
                            if (all_session[index]['stop_at'] and all_session[index + 1]):
                                if (all_session[index]['stop_at'] < all_session[index + 1]['stop_at']):
                                    temp = all_session[index]
                                    all_session[index] = all_session[index + 1]
                                    all_session[index + 1] = temp
                    session = []
                    for x in range(0, config_data['sh_last_no_session']):
                        if x < len(all_session):
                            session.append(all_session[x]['id'])
                    if session:
                        order_data = self.env['pos.order'].search_read([('user_id', '=', self.env.user.id), ('session_id', 'in', session), (
                            'state', '!=', 'cancel'), ('is_return_order', '=', False), ('is_exchange_order', '=', False)], limit=showTo)

            if config_data['sh_load_order_by'] == 'all':
                order_data = self.env['pos.order'].search_read([('user_id', '=', self.env.user.id), (
                    'state', '!=', 'cancel'), ('is_return_order', '=', False), ('is_exchange_order', '=', False)], limit=showTo)

            if config_data['sh_load_order_by'] == 'day_wise':

                if config_data['sh_day_wise_option'] == 'current_day':
                    today_date = datetime.today().strftime('%Y-%m-%d')
                    order_data = self.env['pos.order'].search_read([('user_id', '=', self.env.user.id), ('date_order', '>=', (today_date + " 00:00:00")), (
                        'date_order', '<=', (today_date + " 24:00:00")), ('state', '!=', 'cancel'), ('is_return_order', '=', False), ('is_exchange_order', '=', False)], limit=showTo)

                if config_data['sh_day_wise_option'] == 'last_no_day':
                    if config_data['sh_last_no_days']:
                        today_date = datetime.today().strftime('%Y-%m-%d')
                        last_date = datetime.today() - \
                            timedelta(days=config_data['sh_last_no_days'])
                        last_date = last_date.strftime('%Y-%m-%d')
                        order_data = self.env['pos.order'].search_read([('user_id', '=', self.env.user.id), ('date_order', '<=', (today_date + " 24:00:00")), (
                            'date_order', '>', (last_date + " 24:00:00")), ('state', '!=', 'cancel'), ('is_return_order', '=', False), ('is_exchange_order', '=', False)], limit=showTo)
        order_data = order_data[showFrom:showTo]
        order_line = []
        if order_data and len(order_data) > 0:
            order_ids = []
            for each_order in order_data:
                order_ids.append(each_order.get('id'))
            order_line = self.env['pos.order.line'].search_read(
                [('order_id', 'in', order_ids)])

        return {'order': order_data, 'order_line': order_line}

    def _return_order_total(self):

        for each in self:
            return_order = self.search_read(
                [('old_pos_reference', '=', each.pos_reference), ('is_return_order', '=', True)])
            each.total_return_order = len(return_order)

    def _exchange_order_total(self):

        for each in self:
            exchange_order = self.search_read(
                [('old_pos_reference', '=', each.pos_reference), ('is_exchange_order', '=', True)])
            each.total_exchange_order = len(exchange_order)
#

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['is_return_order'] = ui_order.get(
            'is_return_order') if ui_order.get('is_return_order') else False
        res['is_exchange_order'] = ui_order.get(
            'is_exchange_order') if ui_order.get('is_exchange_order') else False
        res['old_pos_reference'] = ui_order.get(
            'old_pos_reference') if ui_order.get('old_pos_reference') else False
        if ui_order.get('is_return_order'):
            flag = True
            parent_order = self.search(
                [('pos_reference', '=', ui_order['old_pos_reference'])], limit=1)
            updated_lines = ui_order['lines']
            for uptd in updated_lines:
                if uptd[2].get('line_id'):
                    line = self.env['pos.order.line'].search([('order_id', '=', parent_order.id),
                                                              ('id', '=', uptd[2]['line_id'])], limit=1)
                    if not line:
                        line = self.env['pos.order.line'].search(
                            [('order_id', '=', parent_order.id), ('sh_line_id', '=', uptd[2]['old_line_id'])], limit=1)
                    if line:
                        line.sh_return_qty += -(uptd[2]['qty'])
            if parent_order.lines:
                for line in parent_order.lines:
                    if flag:
                        if line.qty > line.sh_return_qty:
                            flag = False

            if flag:
                parent_order.return_status = 'fully_return'
            else:
                parent_order.return_status = 'partialy_return'

        if ui_order.get('is_exchange_order'):
            flag = True
            parent_order = self.search(
                [('pos_reference', '=', ui_order['old_pos_reference'])], limit=1)
            updated_lines = ui_order['lines']
            for uptd in updated_lines:
                if uptd[2].get('line_id'):
                    line = self.env['pos.order.line'].search([('order_id', '=', parent_order.id),
                                                              ('id', '=', uptd[2]['line_id'])], limit=1)
                    if not line:
                        line = self.env['pos.order.line'].search(
                            [('order_id', '=', parent_order.id), ('sh_line_id', '=', uptd[2]['old_line_id'])], limit=1)
                    if line:
                        line.sh_return_qty += -(uptd[2]['qty'])
            if parent_order.lines:
                for line in parent_order.lines:
                    if flag:
                        if line.qty > line.sh_return_qty:
                            flag = False
            if flag:
                parent_order.return_status = 'fully_return'
            else:
                parent_order.return_status = 'partialy_return'

        return res

    @api.model
    def _process_order(self, order, draft, existing_order):
        order_id = super(PosOrder, self)._process_order(
            order, draft, existing_order)
        pos_order = self.search([('id', '=', order_id)])
        old_pos_order = self.search(
            [('pos_reference', '=', pos_order.old_pos_reference)])
        if old_pos_order:
            if pos_order.is_return_order:
                if old_pos_order.old_pos_reference:
                    old_pos_order.write(
                        {'old_pos_reference': old_pos_order.old_pos_reference + ' , ' + pos_order.pos_reference})
                else:
                    old_pos_order.write(
                        {'old_pos_reference': pos_order.pos_reference})
            if pos_order.is_exchange_order:
                if old_pos_order.old_pos_reference:
                    old_pos_order.write(
                        {'old_pos_reference': old_pos_order.old_pos_reference + ' , ' + pos_order.pos_reference})
                else:
                    old_pos_order.write(
                        {'old_pos_reference': pos_order.pos_reference})
        return order_id

    def action_view_return(self):
        return {
            'name': 'Return Order',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('old_pos_reference', '=', self.pos_reference), ('is_return_order', '=', True)],
            'res_model': 'pos.order',
            'target': 'current',
        }

    def action_view_exchange(self):
        return {
            'name': 'Exchange Order',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('old_pos_reference', '=', self.pos_reference), ('is_exchange_order', '=', True)],
            'res_model': 'pos.order',
            'target': 'current',
        }
