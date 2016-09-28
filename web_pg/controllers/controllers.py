# -*- coding: utf-8 -*-
from openerp import http

# class WebPg(http.Controller):
#     @http.route('/web_pg/web_pg/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/web_pg/web_pg/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('web_pg.listing', {
#             'root': '/web_pg/web_pg',
#             'objects': http.request.env['web_pg.web_pg'].search([]),
#         })

#     @http.route('/web_pg/web_pg/objects/<model("web_pg.web_pg"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('web_pg.object', {
#             'object': obj
#         })