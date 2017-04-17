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
        idx_qty_outstanding = 0
        for record in purchase_requisition_line:
            if record.qty_received == 0 :
                idx_qty_received_zero = idx_qty_received_zero + 1
            if record.qty_received > 0 and record.qty_outstanding > 0:
                idx_qty_outstanding = idx_qty_outstanding + 1
        if idx_qty_received_zero == len(purchase_requisition_line) and purchase_requisition.check_missing_product == False :

            super(InheritRequisitionPartner,self).create_order()
            self.create_comparison()

        elif  idx_qty_outstanding > 0 and purchase_requisition.check_missing_product == True:
            self.create_backorder()
            self.create_missing_comparison()

        elif  idx_qty_outstanding > 0 and purchase_requisition.check_missing_product == False and purchase_requisition.validation_check_backorder == True :

            self.create_backorder()
            self.create_backorder_quotation_comparison_form()

        elif idx_qty_received_zero > 0 and purchase_requisition.check_missing_product == False:

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
        order = self.env['purchase.order']
        order_line = self.env['purchase.order.line']
        write_order  = order.search([('requisition_id','=',self._context.get('active_id'))]).write(comparison_data)

        for requisition in purchase_tender.line_ids:
            comparisonline_data={
                'product_qty' : requisition.product_qty,
                # 'qty_request' : requisition.product_qty,
                'comparison_id' : quotation_comparison_form.id
            }
            po = order.search([('requisition_id','=',self._context.get('active_id'))])
            for item in po :
                order_line.search([('order_id','=',item.id),('product_id','=',requisition.product_id.id)]).write(comparisonline_data)

    @api.multi
    def create_missing_comparison(self,context=None):
        purchase_tender = self.env['purchase.requisition'].browse(self._context.get('active_id'))
        quotation_comparison_form = self.env['quotation.comparison.form'].search([('requisition_id','=',self._context.get('active_id')),('validation_missing_product','=',True)])
        order = self.env['purchase.order']
        arrQcfid = []
        for item in quotation_comparison_form:
            arrQcfid.append(item.id)

        #set quotation comparison data
        comparison_data = {
            'source_purchase_request' : purchase_tender.origin,
            'request_id' : purchase_tender.request_id.id,
            'origin' : purchase_tender.complete_name,
            'companys_id' :purchase_tender.companys_id.id,
            'location':purchase_tender.location,
            'type_location' : purchase_tender.type_location,
            'comparison_id' : max(arrQcfid)
        }

        order_line = self.env['purchase.order.line']

        write_order  = order.search([('requisition_id','=',self._context.get('active_id'))]).write(comparison_data)
        # raise exceptions.ValidationError('hahahha')
        purchase_tender.write({'check_missing_product' : False})
        for requisition in purchase_tender.line_ids:
            comparisonline_data={
                'product_qty' : requisition.product_qty,
                # 'qty_request' : requisition.product_qty,
                'comparison_id' : max(arrQcfid)
                # 'comparison_id' : write_order.comparison_id.id
            }
            po = order.search([('requisition_id','=',self._context.get('active_id'))])
            for item in po :
                order_line.search([('order_id','=',item.id),('product_id','=',requisition.product_id.id)]).write(comparisonline_data)


    @api.multi
    def create_backorder_quotation_comparison_form(self):
        for record in self:
            purchase_tender = record.env['purchase.requisition'].browse(record._context.get('active_id'))
            quotation_comparison_form = record.env['quotation.comparison.form'].search([('requisition_id','=',record._context.get('active_id')),('validation_check_backorder','=',True)])
            order = record.env['purchase.order']
            order_line = record.env['purchase.order.line']
            tender_line = record.env['purchase.requisition.line']
            arrPartner = []
            arrProduct = []
            arrOrder = []
            arrQcfid = []
            for item in quotation_comparison_form:
                arrQcfid.append(item.id)

            #set quotation comparison data
            comparison_data = {
                'source_purchase_request' : purchase_tender.origin,
                'request_id' : purchase_tender.request_id.id,
                'origin' : purchase_tender.complete_name,
                'companys_id' :purchase_tender.companys_id.id,
                'location':purchase_tender.location,
                'type_location' : purchase_tender.type_location,
                'comparison_id' : max(arrQcfid)
            }
            tender_line_id = tender_line.search([('requisition_id','=',purchase_tender.id),('qty_outstanding','>',0)])
            order.search([('requisition_id','=',record._context.get('active_id'))]).write(comparison_data)
            purchase_tender.write({'validation_check_backorder' : False})

            for requisition in purchase_tender.line_ids:
                po = order.search([('requisition_id','=',self._context.get('active_id')),('validation_check_backorder','=',True)])
                for item in po :
                    comparisonline_data={
                        'product_qty' : requisition.product_qty,
                        'comparison_id' : max(arrQcfid)
                    }
                    order_line.search([('order_id','=',item.id),('product_id','=',requisition.product_id.id)]).write(comparisonline_data)

            for po in order.search([('requisition_id','=',self._context.get('active_id')),('validation_check_backorder','=',False)]):
                arrPartner.append(po.partner_id.id)

            #intersection partner_id in order line to partner id in wizard,
            intersection_partner = set(arrPartner).intersection(set(record.partner_ids.ids))
            list_partner = list(intersection_partner)

            po_order = order.search([('requisition_id','=',record._context.get('active_id')),('partner_id','in',list_partner),('validation_check_backorder','=',False)])
            for record in po_order:
                arrOrder.append(record.id)
            #Search Price Unit

            for product in tender_line_id:
                arrProduct.append(product.product_id.id)
            poline_order = order_line.search([('product_id','in',arrProduct),('partner_id','in',list_partner),('order_id','=',record.id)])
            try:
                price_unit = min(price.price_unit for price in poline_order)
            except:
                price_unit = 0
            price_data = {'price_unit' :price_unit}

            po = order.search([('requisition_id','=',record._context.get('active_id')),('partner_id','in',list_partner),('validation_check_backorder','=',True)])
            for  purchase in po:
                test = order_line.search([('order_id','=',purchase.id),('partner_id','in',list_partner),('product_id','=',arrProduct)]).write(price_data)


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



