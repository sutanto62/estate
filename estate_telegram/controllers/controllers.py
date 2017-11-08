# -*- coding: utf-8 -*-
from openerp import http

# class EstateTelegram(http.Controller):
#     @http.route('/estate_telegram/estate_telegram/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estate_telegram/estate_telegram/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('estate_telegram.listing', {
#             'root': '/estate_telegram/estate_telegram',
#             'objects': http.request.env['estate_telegram.estate_telegram'].search([]),
#         })

#     @http.route('/estate_telegram/estate_telegram/objects/<model("estate_telegram.estate_telegram"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estate_telegram.object', {
#             'object': obj
#         })