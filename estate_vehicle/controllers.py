# -*- coding: utf-8 -*-
from openerp import http

# class EstateVehicle(http.Controller):
#     @http.route('/estate_vehicle/estate_vehicle/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estate_vehicle/estate_vehicle/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('estate_vehicle.listing', {
#             'root': '/estate_vehicle/estate_vehicle',
#             'objects': http.request.env['estate_vehicle.estate_vehicle'].search([]),
#         })

#     @http.route('/estate_vehicle/estate_vehicle/objects/<model("estate_vehicle.estate_vehicle"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estate_vehicle.object', {
#             'object': obj
#         })