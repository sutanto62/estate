from openerp import models, fields, api, osv, exceptions
from datetime import datetime, date,time
import numpy as np

class WizardPartnerComparison(models.TransientModel):

    _name = 'wizard.partner.comparison'


    partner_ids = fields.Many2many('res.partner', 'quotation_comparison_supplier_rel', 'requisition_id', 'partner_id', string='Vendors', required=True)

    @api.multi
    @api.onchange('check','partner_ids')
    def _onchange_partner_ids(self):
            for item in self:
                    arrPartner = []

                    quotation_comparison_form = item.env['quotation.comparison.form'].browse(self._context.get('active_id'))
                    purchase_tender = item.env['purchase.requisition'].search([('id','=',quotation_comparison_form.requisition_id.id)])
                    partner = item.env['purchase.order'].search([('requisition_id','=',purchase_tender.id)])
                    for record in partner:
                        arrPartner.append(record.partner_id.id)
                    return {
                        'domain':{
                                'partner_ids' : [('id','in',[1] and arrPartner),('state','=','done')]
                        }
                    }

    @api.multi
    def save_partner_quotation(self,context):
        if 'active_id' in context:
            for item in self :
                quotation_comparison_form = item.env['quotation.comparison.form']
                data = {
                'partner_ids':[(6, 0, item.partner_ids.ids)]}

                list_flow=quotation_comparison_form.search([('id','=',context['active_id'])]).write(data)
                item.env['report'].get_action(self, 'purchase_indonesia.report_quotation_comparison_form_document')
                return {'type': 'ir.actions.act_window_close',}
