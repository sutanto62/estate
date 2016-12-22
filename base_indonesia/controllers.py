# -*- coding: utf-8 -*-
from openerp import http

# class BaseIndonesia(http.Controller):
#     @http.route('/base_indonesia/base_indonesia/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/base_indonesia/base_indonesia/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('base_indonesia.listing', {
#             'root': '/base_indonesia/base_indonesia',
#             'objects': http.request.env['base_indonesia.base_indonesia'].search([]),
#         })

#     @http.route('/base_indonesia/base_indonesia/objects/<model("base_indonesia.base_indonesia"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('base_indonesia.object', {
#             'object': obj
#         })