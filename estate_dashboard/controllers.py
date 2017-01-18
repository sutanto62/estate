# -*- coding: utf-8 -*-
from openerp import http

# class ../estate-9.0/estateDashboard(http.Controller):
#     @http.route('/../estate-9.0/estate_dashboard/../estate-9.0/estate_dashboard/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/../estate-9.0/estate_dashboard/../estate-9.0/estate_dashboard/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('../estate-9.0/estate_dashboard.listing', {
#             'root': '/../estate-9.0/estate_dashboard/../estate-9.0/estate_dashboard',
#             'objects': http.request.env['../estate-9.0/estate_dashboard.../estate-9.0/estate_dashboard'].search([]),
#         })

#     @http.route('/../estate-9.0/estate_dashboard/../estate-9.0/estate_dashboard/objects/<model("../estate-9.0/estate_dashboard.../estate-9.0/estate_dashboard"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('../estate-9.0/estate_dashboard.object', {
#             'object': obj
#         })