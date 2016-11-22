# -*- coding: utf-8 -*-
from openerp import http

# class BaseAutoresetSequence(http.Controller):
#     @http.route('/base_autoreset_sequence/base_autoreset_sequence/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/base_autoreset_sequence/base_autoreset_sequence/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('base_autoreset_sequence.listing', {
#             'root': '/base_autoreset_sequence/base_autoreset_sequence',
#             'objects': http.request.env['base_autoreset_sequence.base_autoreset_sequence'].search([]),
#         })

#     @http.route('/base_autoreset_sequence/base_autoreset_sequence/objects/<model("base_autoreset_sequence.base_autoreset_sequence"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('base_autoreset_sequence.object', {
#             'object': obj
#         })