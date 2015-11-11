# -*- coding: utf-8 -*-
from openerp import http

# class EstateNursery(http.Controller):
#     @http.route('/estate_nursery/estate_nursery/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/estate_nursery/estate_nursery/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('estate_nursery.listing', {
#             'root': '/estate_nursery/estate_nursery',
#             'objects': http.request.env['estate_nursery.estate_nursery'].search([]),
#         })

#     @http.route('/estate_nursery/estate_nursery/objects/<model("estate_nursery.estate_nursery"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('estate_nursery.object', {
#             'object': obj
#         })