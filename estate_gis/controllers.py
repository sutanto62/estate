# -*- coding: utf-8 -*-
from openerp import http

# class EstateGis(http.Controller):
#     @http.route('/estate_gis/estate_gis/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estate_gis/estate_gis/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('estate_gis.listing', {
#             'root': '/estate_gis/estate_gis',
#             'objects': http.request.env['estate_gis.estate_gis'].search([]),
#         })

#     @http.route('/estate_gis/estate_gis/objects/<model("estate_gis.estate_gis"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estate_gis.object', {
#             'object': obj
#         })