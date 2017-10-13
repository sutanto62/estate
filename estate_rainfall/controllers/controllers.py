# -*- coding: utf-8 -*-
from openerp import http

# class EstateRainfall(http.Controller):
#     @http.route('/estate_rainfall/estate_rainfall/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estate_rainfall/estate_rainfall/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('estate_rainfall.listing', {
#             'root': '/estate_rainfall/estate_rainfall',
#             'objects': http.request.env['estate_rainfall.estate_rainfall'].search([]),
#         })

#     @http.route('/estate_rainfall/estate_rainfall/objects/<model("estate_rainfall.estate_rainfall"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estate_rainfall.object', {
#             'object': obj
#         })