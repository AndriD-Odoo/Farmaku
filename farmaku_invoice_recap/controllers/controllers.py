# -*- coding: utf-8 -*-
# from odoo import http


# class FarmakuInvoiceRecap(http.Controller):
#     @http.route('/farmaku_invoice_recap/farmaku_invoice_recap/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/farmaku_invoice_recap/farmaku_invoice_recap/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('farmaku_invoice_recap.listing', {
#             'root': '/farmaku_invoice_recap/farmaku_invoice_recap',
#             'objects': http.request.env['farmaku_invoice_recap.farmaku_invoice_recap'].search([]),
#         })

#     @http.route('/farmaku_invoice_recap/farmaku_invoice_recap/objects/<model("farmaku_invoice_recap.farmaku_invoice_recap"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('farmaku_invoice_recap.object', {
#             'object': obj
#         })
