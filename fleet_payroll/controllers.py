# -*- coding: utf-8 -*-
from openerp import http

# class FleetPayroll(http.Controller):
#     @http.route('/fleet_payroll/fleet_payroll/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fleet_payroll/fleet_payroll/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fleet_payroll.listing', {
#             'root': '/fleet_payroll/fleet_payroll',
#             'objects': http.request.env['fleet_payroll.fleet_payroll'].search([]),
#         })

#     @http.route('/fleet_payroll/fleet_payroll/objects/<model("fleet_payroll.fleet_payroll"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fleet_payroll.object', {
#             'object': obj
#         })