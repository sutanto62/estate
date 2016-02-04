# -*- coding: utf-8 -*-
from openerp import http

# class HrIndonesia(http.Controller):
#     @http.route('/hr_indonesia/hr_indonesia/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_indonesia/hr_indonesia/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_indonesia.listing', {
#             'root': '/hr_indonesia/hr_indonesia',
#             'objects': http.request.env['hr_indonesia.hr_indonesia'].search([]),
#         })

#     @http.route('/hr_indonesia/hr_indonesia/objects/<model("hr_indonesia.hr_indonesia"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_indonesia.object', {
#             'object': obj
#         })