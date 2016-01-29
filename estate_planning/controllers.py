# -*- coding: utf-8 -*-
from openerp import http

# class EstatePlanning(http.Controller):
#     @http.route('/estate_planning/estate_planning/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estate_planning/estate_planning/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('estate_planning.listing', {
#             'root': '/estate_planning/estate_planning',
#             'objects': http.request.env['estate_planning.estate_planning'].search([]),
#         })

#     @http.route('/estate_planning/estate_planning/objects/<model("estate_planning.estate_planning"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estate_planning.object', {
#             'object': obj
#         })