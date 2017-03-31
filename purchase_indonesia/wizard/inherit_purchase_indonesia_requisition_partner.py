from openerp import models, fields, api, osv, exceptions
from datetime import datetime, date,time

class InheritRequisitionPartner(models.TransientModel):

    _inherit = 'purchase.requisition.partner'


    def create_backorder(self, cr, uid, ids, context=None):
        active_ids = context and context.get('active_ids', [])
        purchase_requisition = self.pool.get('purchase.requisition')
        for wizard in self.browse(cr, uid, ids, context=context):
            for partner_id in wizard.partner_ids:
                purchase_requisition.make_purchase_backorder(cr, uid, active_ids, partner_id.id, context=context)
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def create_order(self):
        purchase_requisition = self.env['purchase.requisition'].search([('id','=',self._context.get('active_id'))])
        purchase_requisition_line = self.env['purchase.requisition.line'].search([('requisition_id','=',self._context.get('active_id'))])
        idx_qty_received_zero = 0
        for record in purchase_requisition_line:
            if record.qty_received == 0 :
                idx_qty_received_zero = idx_qty_received_zero + 1

        if idx_qty_received_zero == len(purchase_requisition_line) :
            super(InheritRequisitionPartner,self).create_order()
            self.create_comparison()
        else:
            self.create_backorder()
            self.create_backorder_quotation_comparison_form()
        return True

    @api.multi
    def create_comparison(self,context=None):
        purchase_tender = self.env['purchase.requisition'].browse(self._context.get('active_id'))
        quotation_comparison_form = self.env['quotation.comparison.form'].search([('requisition_id','=',self._context.get('active_id'))])

        #set quotation comparison data
        comparison_data = {
            'source_purchase_request' : purchase_tender.origin,
            'request_id' : purchase_tender.request_id.id,
            'origin' : purchase_tender.complete_name,
            'companys_id' :purchase_tender.companys_id.id,
            'location':purchase_tender.location,
            'type_location' : purchase_tender.type_location,
            'comparison_id' : quotation_comparison_form.id
        }
        self.env['purchase.order'].search([('requisition_id','=',self._context.get('active_id'))]).write(comparison_data)

        for requisition in purchase_tender.line_ids:
            comparisonline_data={
                'qty_request' : requisition.product_qty,
                'comparison_id' : quotation_comparison_form.id
            }
            po = self.env['purchase.order'].search([('requisition_id','=',self._context.get('active_id'))])
            for item in po :
                self.env['purchase.order.line'].search([('order_id','=',item.id),('product_id','=',requisition.product_id.id)]).write(comparisonline_data)


    @api.multi
    def create_backorder_quotation_comparison_form(self):
        for record in self:
            purchase_tender = self.env['purchase.requisition'].browse(self._context.get('active_id'))
            quotation_comparison_form = self.env['quotation.comparison.form'].search([('requisition_id','=',self._context.get('active_id')),('validation_check_backorder','=',True)])

            #set quotation comparison data
            comparison_data = {
                'source_purchase_request' : purchase_tender.origin,
                'request_id' : purchase_tender.request_id.id,
                'origin' : purchase_tender.complete_name,
                'companys_id' :purchase_tender.companys_id.id,
                'location':purchase_tender.location,
                'type_location' : purchase_tender.type_location,
                'comparison_id' : quotation_comparison_form.id
            }
            self.env['purchase.order'].search([('requisition_id','=',self._context.get('active_id'))]).write(comparison_data)

            for requisition in purchase_tender.line_ids:
                comparisonline_data={
                    'qty_request' : requisition.product_qty,
                    'comparison_id' : quotation_comparison_form.id
                }
            po = self.env['purchase.order'].search([('requisition_id','=',self._context.get('active_id')),('validation_check_backorder','=',True)])
            for item in po :
                self.env['purchase.order.line'].search([('order_id','=',item.id),('product_id','=',requisition.product_id.id)]).write(comparisonline_data)


    @api.multi
    @api.onchange('partner_ids')
    def _onchange_partner_ids(self):
        for item in self:
            arrPartner=[]

            partner= item.env['res.partner'].search([('state','=','done')])

            for record in partner:
                arrPartner.append(record.id)

            return {
                'domain':{
                    'partner_ids' :[('id','in',arrPartner)]
                }
            }



