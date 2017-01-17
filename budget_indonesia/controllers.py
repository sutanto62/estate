# -*- coding: utf-8 -*-
from openerp import http

# class BudgetIndonesia(http.Controller):
#     @http.route('/budget_indonesia/budget_indonesia/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/budget_indonesia/budget_indonesia/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('budget_indonesia.listing', {
#             'root': '/budget_indonesia/budget_indonesia',
#             'objects': http.request.env['budget_indonesia.budget_indonesia'].search([]),
#         })

#     @http.route('/budget_indonesia/budget_indonesia/objects/<model("budget_indonesia.budget_indonesia"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('budget_indonesia.object', {
#             'object': obj
#         })