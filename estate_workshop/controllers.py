# -*- coding: utf-8 -*-
from openerp import http

# class EstateWorkshop(http.Controller):
#     @http.route('/estate_workshop/estate_workshop/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estate_workshop/estate_workshop/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('estate_workshop.listing', {
#             'root': '/estate_workshop/estate_workshop',
#             'objects': http.request.env['estate_workshop.estate_workshop'].search([]),
#         })

#     @http.route('/estate_workshop/estate_workshop/objects/<model("estate_workshop.estate_workshop"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estate_workshop.object', {
#             'object': obj
#         })