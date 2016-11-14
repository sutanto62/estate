from openerp import models, fields, api, osv, exceptions

class InheritRequisitionPartner(models.TransientModel):

    _inherit = 'purchase.requisition.partner'

    @api.multi
    def create_order(self):
        super(InheritRequisitionPartner,self).create_order()
        self.create_comparison()
        return True

    @api.multi
    def create_comparison(self,context=None):
        for purchase_tender in self.env['purchase.requisition'].browse(self._context.get('active_id')):
            purchase_data = {
                'company_id': purchase_tender.companys_id.id,
                'date_pp': purchase_tender.schedule_date,
                'requisition_id': purchase_tender.id,
                'origin' : purchase_tender.origin,
                'type_location' : purchase_tender.type_location
            }
            res = self.env['quotation.comparison.form'].create(purchase_data)
            comparison_data = {
                'comparison_id' : res.id
            }
            self.env['purchase.order'].search([('requisition_id','=',self._context.get('active_id'))]).write(comparison_data)
            po = self.env['purchase.order'].search([('requisition_id','=',self._context.get('active_id'))])
            self.env['purchase.order.line'].search([('order_id','=',po.id)]).write(comparison_data)
        return True


