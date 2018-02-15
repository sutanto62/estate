# -*- coding: utf-8 -*-
from openerp import http

# class EstateStock(http.Controller):
#     @http.route('/estate_stock/estate_stock/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estate_stock/estate_stock/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('estate_stock.listing', {
#             'root': '/estate_stock/estate_stock',
#             'objects': http.request.env['estate_stock.estate_stock'].search([]),
#         })

#     @http.route('/estate_stock/estate_stock/objects/<model("estate_stock.estate_stock"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estate_stock.object', {
#             'object': obj
#         })