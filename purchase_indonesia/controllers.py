# -*- coding: utf-8 -*-
from openerp import http

# class EstateProcurment(http.Controller):
#     @http.route('/estate_procurement/estate_procurement/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estate_procurement/estate_procurement/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('estate_procurement.listing', {
#             'root': '/estate_procurement/estate_procurement',
#             'objects': http.request.env['estate_procurement.estate_procurement'].search([]),
#         })

#     @http.route('/estate_procurement/estate_procurement/objects/<model("estate_procurement.estate_procurement"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estate_procurement.object', {
#             'object': obj
#         })