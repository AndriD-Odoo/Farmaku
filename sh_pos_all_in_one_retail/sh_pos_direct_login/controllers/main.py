# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo.addons.web.controllers.main import Home as Home
from odoo.http import request
from odoo import http


class Home(Home):

    @http.route(website=True, auth="public", sitemap=False)
    def web_login(self, redirect=None, *args, **kw):
        response = super(Home, self).web_login(redirect=redirect, *args, **kw)
        request.params['login_success'] = False
        if not redirect and request.params['login_success']:

            if request.env['res.users'].browse(request.uid).has_group('base.group_user'):
                if request.uid:
                    res_users_obj = request.env['res.users']
                    search_user = res_users_obj.search(
                        [('id', '=', request.uid)], limit=1)
                    if search_user and search_user.pos_config_id:
                        if search_user.pos_config_id.pos_session_state == 'opening_control' and search_user.pos_config_id.pos_session_username == request.env.user.name:
                            search_user.pos_config_id.open_session_cb()
                            redirect = '/pos/web'

                        elif search_user.pos_config_id.current_session_state == 'opened' and search_user.pos_config_id.pos_session_username == request.env.user.name:
                            redirect = '/pos/web'

                        else:
                            redirect = '/web'
            else:
                redirect = '/my'
            return http.redirect_with_hash(redirect)
        return response

    def _login_redirect(self, uid, redirect=None):

        res_users_obj = request.env['res.users']
        if uid:
            search_user = res_users_obj.search([('id', '=', uid)], limit=1)
            if search_user and search_user.pos_config_id:
                if not search_user.pos_config_id.pos_session_state and not search_user.pos_config_id.pos_session_username:
                    search_user.pos_config_id.open_session_cb()
                    return redirect if redirect else '/pos/web'

                elif search_user.pos_config_id.current_session_state == 'opened' and search_user.pos_config_id.pos_session_username == request.env.user.name:
                    return '/pos/web'
                else:
                    return redirect if redirect else '/web'

        return redirect if redirect else '/web'
