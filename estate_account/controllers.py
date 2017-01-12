# -*- coding: utf-8 -*-
from openerp import http

# class ../estate-9.0/estateAccount(http.Controller):
#     @http.route('/../estate-9.0/estate_account/../estate-9.0/estate_account/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/../estate-9.0/estate_account/../estate-9.0/estate_account/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('../estate-9.0/estate_account.listing', {
#             'root': '/../estate-9.0/estate_account/../estate-9.0/estate_account',
#             'objects': http.request.env['../estate-9.0/estate_account.../estate-9.0/estate_account'].search([]),
#         })

#     @http.route('/../estate-9.0/estate_account/../estate-9.0/estate_account/objects/<model("../estate-9.0/estate_account.../estate-9.0/estate_account"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('../estate-9.0/estate_account.object', {
#             'object': obj
#         })