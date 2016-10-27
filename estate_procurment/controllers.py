# -*- coding: utf-8 -*-
from openerp import http

# class EstateProcurment(http.Controller):
#     @http.route('/estate_procurment/estate_procurment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estate_procurment/estate_procurment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('estate_procurment.listing', {
#             'root': '/estate_procurment/estate_procurment',
#             'objects': http.request.env['estate_procurment.estate_procurment'].search([]),
#         })

#     @http.route('/estate_procurment/estate_procurment/objects/<model("estate_procurment.estate_procurment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estate_procurment.object', {
#             'object': obj
#         })