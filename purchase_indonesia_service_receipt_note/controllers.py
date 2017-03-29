# -*- coding: utf-8 -*-
from openerp import http

# class PurchaseServiceReceiptNote(http.Controller):
#     @http.route('/purchase_indonesia_service_receipt_note/purchase_indonesia_service_receipt_note/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_indonesia_service_receipt_note/purchase_indonesia_service_receipt_note/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_indonesia_service_receipt_note.listing', {
#             'root': '/purchase_indonesia_service_receipt_note/purchase_indonesia_service_receipt_note',
#             'objects': http.request.env['purchase_indonesia_service_receipt_note.purchase_indonesia_service_receipt_note'].search([]),
#         })

#     @http.route('/purchase_indonesia_service_receipt_note/purchase_indonesia_service_receipt_note/objects/<model("purchase_indonesia_service_receipt_note.purchase_indonesia_service_receipt_note"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_indonesia_service_receipt_note.object', {
#             'object': obj
#         })