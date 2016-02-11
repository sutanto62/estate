# -*- coding: utf-8 -*-
from openerp import http

# class EstatePlanting(http.Controller):
#     @http.route('/estate_planting/estate_planting/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estate_planting/estate_planting/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('estate_planting.listing', {
#             'root': '/estate_planting/estate_planting',
#             'objects': http.request.env['estate_planting.estate_planting'].search([]),
#         })

#     @http.route('/estate_planting/estate_planting/objects/<model("estate_planting.estate_planting"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estate_planting.object', {
#             'object': obj
#         })