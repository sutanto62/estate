from openerp import models, fields, api, osv, exceptions

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
        purchase_requisition_line = self.env['purchase.requisition.line'].search([('requisition_id','=',self._context.get('active_id'))])
        for record in purchase_requisition_line:
            if record.qty_received == 0 :
                super(InheritRequisitionPartner,self).create_order()
                self.create_comparison()
            elif record.qty_received > 0:
                self.create_backorder()
        return True

    @api.multi
    def create_comparison(self,context=None):
        purchase_tender = self.env['purchase.requisition'].browse(self._context.get('active_id'))
        quotation_comparison_form = self.env['quotation.comparison.form'].search([('requisition_id','=',self._context.get('active_id'))])

        #set quotation comparison data
        comparison_data = {
            'source_purchase_request' : purchase_tender.origin,
            'origin' : purchase_tender.complete_name,
            'companys_id' :purchase_tender.companys_id.id,
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



