# -*- coding: utf-8 -*-
from openerp import http

# class ../estate-production/hrFingerprintReport(http.Controller):
#     @http.route('/../estate-production/hr_fingerprint_report/../estate-production/hr_fingerprint_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/../estate-production/hr_fingerprint_report/../estate-production/hr_fingerprint_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('../estate-production/hr_fingerprint_report.listing', {
#             'root': '/../estate-production/hr_fingerprint_report/../estate-production/hr_fingerprint_report',
#             'objects': http.request.env['../estate-production/hr_fingerprint_report.../estate-production/hr_fingerprint_report'].search([]),
#         })

#     @http.route('/../estate-production/hr_fingerprint_report/../estate-production/hr_fingerprint_report/objects/<model("../estate-production/hr_fingerprint_report.../estate-production/hr_fingerprint_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('../estate-production/hr_fingerprint_report.object', {
#             'object': obj
#         })