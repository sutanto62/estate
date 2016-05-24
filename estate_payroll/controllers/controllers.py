# -*- coding: utf-8 -*-
from openerp import http

# class EstatePayroll(http.Controller):
#     @http.route('/estate_payroll/estate_payroll/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estate_payroll/estate_payroll/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('estate_payroll.listing', {
#             'root': '/estate_payroll/estate_payroll',
#             'objects': http.request.env['estate_payroll.estate_payroll'].search([]),
#         })

#     @http.route('/estate_payroll/estate_payroll/objects/<model("estate_payroll.estate_payroll"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estate_payroll.object', {
#             'object': obj
#         })