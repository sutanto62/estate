# -*- coding: utf-8 -*-
from openerp import http

# class EstateHk21(http.Controller):
#     @http.route('/estate_hk_21/estate_hk_21/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estate_hk_21/estate_hk_21/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('estate_hk_21.listing', {
#             'root': '/estate_hk_21/estate_hk_21',
#             'objects': http.request.env['estate_hk_21.estate_hk_21'].search([]),
#         })

#     @http.route('/estate_hk_21/estate_hk_21/objects/<model("estate_hk_21.estate_hk_21"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estate_hk_21.object', {
#             'object': obj
#         })