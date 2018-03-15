from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
from dateutil.relativedelta import *
import calendar
from openerp.tools import (DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT,drop_view_if_exists)


class InheritPurchaseTenders(models.Model):

    def return_action_to_open(self, cr, uid, ids, context=None):
        """ This opens the xml view specified in xml_id for the current Quotation Comparison """
        if context is None:
            context = {}
        if context.get('xml_id'):
            res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid ,'purchase_indonesia', context['xml_id'], context=context)
            res['context'] = context
            res['context'].update({'default_requisition_id': ids[0]})
            res['domain'] = [('requisition_id','=', ids[0])]
            return res
        return False

    _inherit = 'purchase.requisition'
    _description = 'inherit purchase requisition'
    _order = 'ordering_date asc'
    _rec_name = 'complete_name'

    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    type_location = fields.Char('Location')
    state = fields.Selection(selection_add = [('rollback','Roll Back PP'),
                                              ('closed','PP Closed'),
                                              ('open', 'PP Outstanding'),
                                              ('done', 'Shipment')])
    validation_check_backorder = fields.Boolean('Confirm backorder')
    validation_missing_product = fields.Boolean('Missing Product',compute='compute_validation_check_product')
    location = fields.Char('Location')
    companys_id = fields.Many2one('res.company','Company')
    request_id = fields.Many2one('purchase.request','Purchase Request')
    due_date = fields.Date('Due Date',compute='_compute_due_date')
    validation_due_date = fields.Boolean('Validation Due Date',compute='_compute_validation_due_date')
    quotation_state = fields.Char('QCF state',compute='_compute_quotation_state')
    validation_correction = fields.Boolean('Validation Correction',compute='_compute_validation_correction')
    validation_qcf = fields.Boolean('Validation QCF',compute='_compute_validation_qcf')
    validation_button_correction = fields.Boolean('Validation Button Correction',compute='_compute_button_correction')
    check_missing_product = fields.Boolean('Check Missing Product')
    force_closing = fields.Boolean('Force Closing Tender')
    comparison_id = fields.Integer('Comparison ID')
    check_backorder = fields.Boolean('Check Backorder',compute='compute_validation_check_backorder')
    #Please check class TriggerPurchaseTender below to know detail triggers that update is_po_done, is_grn_done and is_inv_done
    is_qcf_done = fields.Boolean('Quotation', store=True)
    is_po_done = fields.Boolean('PO', store=True)
    is_grn_done = fields.Boolean('GRN/SRN', store=True)
    is_inv_done = fields.Boolean('Invoice', store=True)
    is_pp_confirmation = fields.Boolean('PP Confirmation',compute='_compute_is_confirmation')
    total_estimate_price = fields.Float('Total Estimate Price', compute='_compute_total_estimate_price')
    pp_description = fields.Char('Description', compute='_compute_pp_description')
    is_qcf_draft = fields.Boolean('Is QCF Draft', compute='_compute_is_qcf_draft')
    first_product_name = fields.Char('First Product Name', compute='_compute_first_product_name')
    max_grn_date = fields.Date('Completion Date', compute='_compute_max_grn_date')
    is_spec_not_clear = fields.Boolean('Spec Not Yet Clear', store=True)
    
    @api.multi
    def _compute_first_product_name(self):
        for item in self:
            if item.line_ids :
                item.first_product_name = item.line_ids[0].product_id.name
                
    @api.multi
    def _compute_max_grn_date(self):
        for item in self :
            if item.request_id :
                pickings = self.env['stock.picking'].search([('pr_source', 'like', item.request_id.complete_name)])
                for i in pickings :
                    for mids in i.message_ids:
                        for mids_tracking in mids.tracking_value_ids:
                            if mids_tracking.field == 'state' and (mids_tracking.new_value_char == 'Done' or mids_tracking.new_value_char == 'selesai'):
                                item.max_grn_date = mids.date
        
    @api.multi
    def _compute_is_qcf_draft(self):
        for item in self:
            qcf = self.env['quotation.comparison.form'].search([('requisition_id','=',self.id),('state','=','draft')])
            item.is_qcf_draft = True if len(qcf) > 0 else False
        
    @api.multi
    def _compute_pp_description(self):
        for item in self:
            item.pp_description = item.request_id.description
    
    @api.multi
    def _compute_total_estimate_price(self):
        for item in self:
            item.total_estimate_price = item.request_id.total_estimate_price
    
    @api.multi
    def _compute_is_confirmation(self):
        for item in self:
            item.is_pp_confirmation = item.request_id.is_confirmation
    
    # todo compute is_qcf_done, is_po_done, is_inv_done store = true
#     @api.model
#     def set_status_po_grn_inv(self):
#         print 'set_status_po_grn_inv'
#         for item in self:
#             purch_req = item.env['purchase.request.line']
#             purch_req_lines = purch_req.search([('request_id','=',item.request_id.id)])
#              
#             state_purch_order = ['done','purchase']
#             purch_order = item.env['purchase.order']
#             purch_orders = purch_order.search([('request_id','=',item.request_id.id),('state','in',state_purch_order)])
#             purch_order_lines = item.env['purchase.order.line'].search([('order_id','in',purch_orders.ids)])
#              
#             stock_picking = item.env['stock.picking']
#             stock_pickings = stock_picking.search([('purchase_id','in',purch_orders.ids),('state','=','done')])
#             stock_pack_operations = item.env['stock.pack.operation'].search([('picking_id','in',stock_pickings.ids)])
#              
#             state_acc_inv = ['open','paid']
#             acc_inv = item.env['account.invoice']
#             acc_invs = acc_inv.search([('picking_id','in',stock_pickings.ids),('state','in',state_acc_inv)])
#              
#             #if acc_invs null it means invoice is created per po not per grn.
#             if not acc_invs:
#                 acc_inv_lines = item.env['account.invoice.line'].search([('purchase_line_id.order_id.id','in',purch_orders.ids)])
#             else:
#                 acc_inv_lines = item.env['account.invoice.line'].search([('invoice_id','in',acc_invs.ids)])
#                  
#             l_purch_req_lines = []
#             str_product_qty = ''
#             for i in purch_req_lines:
#                 str_product_qty = str(i.product_id.id) + '-' + str(i.product_qty)
#                 l_purch_req_lines.extend(str_product_qty)
#                  
#             l_purch_order_lines = []
#             str_product_qty = ''
#             for i in purch_order_lines:
#                 str_product_qty = str(i.product_id.id) + '-' + str(i.product_qty)
#                 l_purch_order_lines.extend(str_product_qty)
#                  
#             l_stock_pack_operations = []
#             str_product_qty = ''
#             for i in stock_pack_operations:
#                 str_product_qty = str(i.product_id.id) + '-' + str(i.product_qty)
#                 l_stock_pack_operations.extend(str_product_qty)
#              
#             l_acc_inv_lines = []
#             str_product_qty = ''
#             for i in acc_inv_lines:
#                 str_product_qty = str(i.product_id.id) + '-' + str(i.quantity)
#                 l_acc_inv_lines.extend(str_product_qty)
#              
#             item.is_po_done = set(l_purch_req_lines) == set(l_purch_order_lines)
#             item.is_grn_done = set(l_purch_req_lines) == set(l_stock_pack_operations)
#             item.is_inv_done = set(l_purch_req_lines) == set(l_acc_inv_lines)
    
    @api.multi
    def set_is_confirmation_true(self):
        for item in self:
            item.request_id.set_is_confirmation(True)
            
    @api.multi
    def set_is_confirmation_false(self):
        for item in self:
            item.request_id.set_is_confirmation(False)
        
    @api.multi
    def update_status_po_grn_inv(self):
        for item in self:
            purch_req = item.env['purchase.request.line']
            purch_req_lines = purch_req.search([('request_id','=',item.request_id.id)])
            
            state_purch_order = ['done','purchase']
            purch_order = item.env['purchase.order']
            purch_orders = purch_order.search([('request_id','=',item.request_id.id),('state','in',state_purch_order)])
            purch_order_lines = item.env['purchase.order.line'].search([('order_id','in',purch_orders.ids)])
            
            stock_picking = item.env['stock.picking']
            stock_pickings = stock_picking.search([('purchase_id','in',purch_orders.ids),('state','=','done')])
            stock_pack_operations = item.env['stock.pack.operation'].search([('picking_id','in',stock_pickings.ids)])
            
            state_acc_inv = ['open','paid']
            acc_inv = item.env['account.invoice']
            acc_invs = acc_inv.search([('picking_id','in',stock_pickings.ids),('state','in',state_acc_inv)])
            
            #if acc_invs null it means invoice is created per po not per grn.
            if not acc_invs:
                acc_inv_lines = item.env['account.invoice.line'].search([('purchase_line_id.order_id.id','in',purch_orders.ids)])
            else:
                acc_inv_lines = item.env['account.invoice.line'].search([('invoice_id','in',acc_invs.ids)])
                
            l_purch_req_lines = []
            str_product_qty = ''
            for i in purch_req_lines:
                str_product_qty = str(i.product_id.id) + '-' + str(i.product_qty)
                l_purch_req_lines.extend(str_product_qty)
                
            l_purch_order_lines = []
            str_product_qty = ''
            for i in purch_order_lines:
                str_product_qty = str(i.product_id.id) + '-' + str(i.product_qty)
                l_purch_order_lines.extend(str_product_qty)
                
            l_stock_pack_operations = []
            str_product_qty = ''
            for i in stock_pack_operations:
                str_product_qty = str(i.product_id.id) + '-' + str(i.product_qty)
                l_stock_pack_operations.extend(str_product_qty)
            
            l_acc_inv_lines = []
            str_product_qty = ''
            for i in acc_inv_lines:
                str_product_qty = str(i.product_id.id) + '-' + str(i.quantity)
                l_acc_inv_lines.extend(str_product_qty)
            
            item.is_po_done = set(l_purch_req_lines) == set(l_purch_order_lines)
            item.is_grn_done = set(l_purch_req_lines) == set(l_stock_pack_operations)
            item.is_inv_done = set(l_purch_req_lines) == set(l_acc_inv_lines)
            
    @api.multi
    def _get_value_low(self):
        #get Minimal value from purchase params for Purchase Request

        value_standard = self.env['purchase.params.setting'].search([('name','=',self._name)])

        price = min(value.value_params for value in value_standard)

        return float(price)

    @api.multi
    def _get_user(self):
        #find User
        user= self.env['res.users'].browse(self.env.uid)

        return user

    @api.multi
    def tender_in_progress(self):
        for item in self:
            super(InheritPurchaseTenders,item).tender_in_progress()
            data={
                'user_id':item._get_user().id
            }
            item.write(data)
            item._change_created_by_qcf()
            return True

    @api.multi
    def tender_open(self):
        for item in self:
            count_order = 0
            order = item.env['purchase.order'].search([('requisition_id','=',item.id),('state','in',['draft'])])
            for record in order:
                if len(record) > 0 :
                    count_order = count_order + 1
            if (count_order == 0):
                super(InheritPurchaseTenders,item).tender_open()
            else:
                msg_error = 'You Must Proceed Your Order'
                raise exceptions.ValidationError(msg_error)

    @api.multi
    def tender_state_closed(self):
        for item in self:
            tracking = item.env['validate.tracking.purchase.order.invoice'].search([('requisition_id','=',item.id)])
            for record in tracking:
                if (record.sum_quantity_tender == record.sum_quantity_purchase) and (record.sum_quantity_tender == record.sum_quantity_picking) and (record.sum_quantity_tender == record.sum_quantity_invoice):
                    return item.write({'state':'closed'})
                elif item.force_closing == True and ((record.sum_quantity_tender == record.sum_quantity_purchase) and (record.sum_quantity_tender == record.sum_quantity_picking) and (record.sum_quantity_tender == record.sum_quantity_invoice)):
                    return item.write({'state':'closed'})
                elif item.force_closing == True:
                    return item.write({'state':'closed'})
                else:
                    raise exceptions.ValidationError('You Must Complete Your Purchase Order')


    @api.multi
    def _change_created_by_qcf(self):
        data = {
            'pic_id': self.user_id.id
        }
        res = self.env['quotation.comparison.form'].search([('requisition_id','=',self.id)]).write(data)

    @api.multi
    @api.depends('request_id')
    def _compute_validation_correction(self):

        for item in self:
            arrOutstanding = []
            domain = [('requisition_id','=',item.id),('check_missing_product','=',False),('qty_outstanding','>',0)]

            for line in item.line_ids.search(domain):
                arrOutstanding.append(line.id)

            if (item.request_id.validation_correction_procurement == True and item.request_id.state in ['done','approved'] and item.validation_missing_product == False) or (item.request_id.validation_correction_procurement == False and item.state not in ['draft','done','open','closed'] and item.validation_missing_product == False) :

                item.validation_correction = True
            elif (item.request_id.validation_correction_procurement == False and item.state in ['in_progress','done','open']) and item.validation_missing_product == True:

                item.validation_correction = False

            else:
               if item.validation_check_backorder == True and len(arrOutstanding) > 0:

                   item.validation_correction = True

               elif item.validation_check_backorder == False and item.state in ['draft','open','done','closed'] and item.check_missing_product == False:

                   item.validation_correction = False

               elif item.validation_missing_product == False and item.check_missing_product == True:

                   item.validation_correction = True

               else:

                   item.validation_correction = False

    @api.multi
    @api.depends('validation_check_backorder')
    def compute_validation_check_backorder(self):
        for record in self:
            arrOutstanding = []
            arrMissing = []
            domain = [('requisition_id','=',record.id),('check_missing_product','=',False),('qty_outstanding','>',0)]
            domain2 = [('requisition_id','=',record.id),('check_missing_product','=',True)]
            
            qcf = self.env['quotation.comparison.form'].search([('requisition_id','=',self.id),('state','=','draft')])

            for line in record.line_ids.search(domain2):
                arrMissing.append(line.id)
            for line in record.line_ids.search(domain):
                arrOutstanding.append(line.id)

            if record.state in ['draft','cancel','closed'] or len(qcf) > 0:
                record.check_backorder = True
            else:
                if record.validation_check_backorder == False and len(arrOutstanding) > 0 and len(arrMissing) > 0:
                    record.check_backorder = True
                elif record.validation_check_backorder == False and len(arrOutstanding) > 0 and len(arrMissing) == 0:
                    record.check_backorder = False
                else:
                    record.check_backorder = True

    @api.multi
    @api.depends('purchase_ids')
    def compute_validation_check_product(self):
        for item in self:
            #change Validation missing Product

            if item.state in ['open']:
                if len(item.purchase_ids.search([('requisition_id','=',item.id),('state','in',('purchase','received_all','received_force_done'))])) > 0:
                    item.validation_missing_product = item.checking_validation_missing_and_backorder()
                    if item.validation_missing_product == True:
                        item.change_line_tender_missing()
            elif item.state in ['in_progress']:

                if len(item.purchase_ids.search([('requisition_id','=',item.id),('state','=','purchase')])) > 0:
                    item.validation_missing_product = item.checking_validation_missing_and_backorder()
                    if item.validation_missing_product == True:
                        item.change_line_tender_missing()

    @api.multi
    def checking_validation_missing_and_backorder(self):
        for item in self:

                #search Missing Product or Outstanding product starts Here

                arrOutstanding = []
                arrMissing = []

                domain = [('requisition_id','=',item.id),('check_missing_product','=',False),('qty_outstanding','>',0)]

                domain2 = [('requisition_id','=',item.id),('check_missing_product','=',True)]

                for line in item.line_ids.search(domain):
                    arrOutstanding.append(line.id)

                for line in item.line_ids.search(domain2):
                    arrMissing.append(line.id)

                if list(item.list_product()) != [] and item.check_missing_product == False:
                    validation_missing_product = True
                elif list(item.list_product()) != [] and item.check_missing_product == True:
                    validation_missing_product = False
                else:
                    validation_missing_product = False

                    if len(arrOutstanding) > 0 and len(arrMissing) == 0 :
                        validation_missing_product = False
                    elif len(arrOutstanding) > 0 and len(arrMissing) > 0 :
                        validation_missing_product = True

                return validation_missing_product

    @api.multi
    def list_product(self):
        for item in self:
            #to list product if check back order missing is True
            arrProductLine = []
            arrPurchase = []
            arrPurchaseProduct = []
            tender_line = item.env['purchase.requisition.line']
            purchase = item.env['purchase.order']
            purchase_line = item.env['purchase.order.line']

            product_tender_line = tender_line.search([('requisition_id','=',item.id)])
            for product in product_tender_line:
                arrProductLine.append(product.product_id.id)

            purchase_id = purchase.search([('requisition_id','=',item.id),('state','in',['purchase','done','received_all','received_force_done']),('validation_check_backorder','=',False)])
            for purchase in purchase_id:
                arrPurchase.append(purchase.id)
            purchase_line_id = purchase_line.search([('order_id','in',arrPurchase)])

            for product_purchase in purchase_line_id:
                arrPurchaseProduct.append(product_purchase.product_id.id)

            set_product = set(arrProductLine) - set(arrPurchaseProduct)

            return set_product

    @api.multi
    def change_line_tender_missing(self):
        for item in self:
            #change Line tender Missing in Requisition line
            tender_line = item.env['purchase.requisition.line']
            line_tender_missing = tender_line.search([('requisition_id','=',item.id),('product_id','in',list(item.list_product()))])
            line_tender_missing.write({'check_missing_product' : True})

    @api.multi
    @api.depends('purchase_ids')
    def _compute_button_correction(self):

        for item in self:
            count_order = 0
            order = item.env['purchase.order'].search([('requisition_id','=',item.id),('state','in',['purchase','done','receive_all','receive_force_done'])])
            for record in order:
                if len(record) > 0 :
                    count_order = count_order + 1
            if (count_order == 0) and item.state in('in_progress'):
                item.validation_button_correction = True
            else:
                item.validation_button_correction = False

    @api.multi
    @api.depends('purchase_ids')
    def _compute_validation_qcf(self):
        for item in self:
            count_confirm = 0
            count_purchase = len(item.purchase_ids)
            order = item.env['purchase.order'].search([('requisition_id','=',item.id),('state','in',['draft','sent'])])
            count_order = len(order)
            if count_purchase > 0:
                for record in order:
                    if record.validation_check_confirm_vendor == True:
                        count_confirm = count_confirm + 1
                    if count_order == count_confirm:
                        item.validation_qcf = True
                    elif (count_order == count_confirm) and (record.validation_check_backorder == True):
                        item.validation_qcf = True
                    else:
                        if item.state in ['draft','cancel','closed','done','rollback']:
                            item.validation_qcf = False


    @api.multi
    @api.depends('quotation_state')
    def _compute_quotation_state(self):
        for item in self:
            domain1 = [('requisition_id','=',item.id)]
            qcf = item.env['quotation.comparison.form'].search(domain1)
            count_qcf = len(qcf)
            index_a = 0
            if count_qcf > 1:
                for record in qcf:
                    if record.state == 'done':
                        index_a = index_a + 1
                if index_a == count_qcf:
                    qcf_state = 'QCF Done'
                    item.quotation_state = qcf_state
                else :
                    qcf_state = 'In Progress QCF'
                    item.quotation_state = qcf_state
            else:
                qcf_state = qcf.state
                categ_state = dict(qcf._columns['state'].selection).get(qcf_state)

                if qcf_state in [True,False]:
                    item.quotation_state = qcf_state
                else:
                    item.quotation_state = categ_state

    @api.multi
    def purchase_request_correction(self):
        for item in self:
            item.state = 'rollback'
            purchase_request = item.env['purchase.request'].search([('id','=',item.request_id.id)])
            update_purchase_request = purchase_request.write({
                'state':'budget' if purchase_request._get_max_price() < purchase_request._get_price_low() else'approval4' ,
                'assigned_to' : purchase_request._get_budget_manager() if purchase_request._get_max_price() < purchase_request._get_price_low() else purchase_request._get_division_finance(),
                'validation_correction_procurement' : True
            })
            item.send_mail_template()


    @api.multi
    def create_backorder_quotation_comparison_form(self):
        for record in self:
            purchase_requisition = record.env['purchase.requisition'].search([('id','=',record.id)])
            try:
                company_code = record.env['res.company'].search([('id','=',record.companys_id.id)]).code
            except:
                raise exceptions.ValidationError('Company Code is Null')
            sequence_name = 'quotation.comparison.form.'+record.request_id.code.lower()+'.'+company_code.lower()
            purchase_data = {
                    'name' : record.env['ir.sequence'].next_by_code(sequence_name),
                    'company_id': purchase_requisition.companys_id.id,
                    'date_pp': datetime.today(),
                    'requisition_id': purchase_requisition.id,
                    'origin' : purchase_requisition.origin,
                    'type_location' : purchase_requisition.type_location,
                    'location':purchase_requisition.location,
                    'state':'draft',
                    'pic_id': record.user_id.id,

                    'validation_check_backorder':True
                }
            arrOutstanding = []
            domain = [('requisition_id','=',record.id),('check_missing_product','=',False),('qty_outstanding','>',0)]

            for line in record.line_ids.search(domain):
                arrOutstanding.append(line.id)

            if len(arrOutstanding) > 0:
                res = record.env['quotation.comparison.form'].create(purchase_data)
                record.write({'validation_check_backorder' : True})
                quotation_comparison_form = self.env['quotation.comparison.form'].search([('requisition_id','=',record.id),('validation_check_backorder','=',True)])
                arrQcfid = []
                for item in quotation_comparison_form:
                    arrQcfid.append(item.id)
                data = {
                    'comparison_id' : max(arrQcfid)
                }
                record.write(data)
            else:
                raise exceptions.ValidationError('You Cannot Run This Process, cause no product have Qty OutStanding')

    @api.multi
    def create_missing_product_quotation_comparison_form(self):
        for record in self:
            purchase_requisition = record.env['purchase.requisition'].search([('id','=',record.id)])
            try:
                company_code = record.env['res.company'].search([('id','=',record.companys_id.id)]).code
            except:
                raise exceptions.ValidationError('Company Code is Null')
            sequence_name = 'quotation.comparison.form.'+record.request_id.code.lower()+'.'+company_code.lower()
            purchase_data = {
                    'name' : record.env['ir.sequence'].next_by_code(sequence_name),
                    'company_id': purchase_requisition.companys_id.id,
                    'date_pp': datetime.today(),
                    'requisition_id': purchase_requisition.id,
                    'origin' : purchase_requisition.origin,
                    'type_location' : purchase_requisition.type_location,
                    'location':purchase_requisition.location,
                    'state':'draft',
                    'pic_id': record.user_id.id,

                    'validation_missing_product':True
                }
            record.check_missing_product = True
            res = record.env['quotation.comparison.form'].create(purchase_data)
            quotation_comparison_form = self.env['quotation.comparison.form'].search([('requisition_id','=',record.id),('validation_missing_product','=',True)])
            arrQcfid = []
            for item in quotation_comparison_form:
                arrQcfid.append(item.id)
            data = {
                'comparison_id' : max(arrQcfid)
            }
            record.write(data)

    @api.multi
    def _compute_date(self):
        arrMinDateNorm = []
        arrMaxDateNorm = []

        arrMinDateUrgent = []
        arrMaxDateUrgent = []
        res = []
        fmt = '%Y-%m-%d'
        normal = self.env['purchase.indonesia.type'].search([('name','in',['Normal','normal'])])
        urgent = self.env['purchase.indonesia.type'].search([('name','in',['Urgent','urgent'])])
        for item in normal:
            arrMaxDateNorm.append(item.max_days)
            arrMinDateNorm.append(item.min_days)

        for item in urgent:
            arrMaxDateUrgent.append(item.max_days)
            arrMinDateUrgent.append(item.min_days)

        compute = self.due_date
        try:
            fromdt = self.request_id.date_start
            init_date=datetime.strptime(str(fromdt),fmt)
        except:
            fromdt = date.today()
            init_date=datetime.strptime(str(fromdt),fmt)

        if self.request_id.type_purchase.name in ['Normal','normal']:
            min_days = arrMinDateNorm[0]
            max_days = arrMaxDateNorm[0]

            if self.request_id.code == 'KPST':
                 date_after_month = datetime.date(init_date) + relativedelta(days=min_days)
                 compute = date_after_month.strftime(fmt)

            elif self.request_id.code in ['KOKB','KPWK']:
                 date_after_month = datetime.date(init_date) + relativedelta(days=max_days)
                 compute = date_after_month.strftime(fmt)

        elif self.request_id.type_purchase.name in ['Urgent','urgent']:
            min_days = arrMinDateUrgent[0]
            max_days = arrMaxDateUrgent[0]
            if self.request_id.code == 'KPST':
                 date_after_month = datetime.date(init_date)+ relativedelta(days=min_days)
                 compute = date_after_month.strftime(fmt)

            elif self.request_id.code in ['KOKB','KPWK']:
                 date_after_month = datetime.date(init_date)+ relativedelta(days=max_days)
                 compute = date_after_month.strftime(fmt)
        res = compute
        return res

    @api.multi
    @api.depends('request_id')
    def _compute_due_date(self):
        for item in self:
            item.due_date = item._compute_date()

    @api.multi
    @api.depends('due_date')
    def _compute_validation_due_date(self):
        standard_due_date = self._get_value_low()
        fmt = '%Y-%m-%d'
        for item in self:
            try:
                fromdt = item.due_date
                init_date=datetime.strptime(str(fromdt),fmt)
                date_after_month = datetime.date(init_date)-relativedelta(days=standard_due_date)
            except:
                date_after_month = datetime.now()

            compute = date_after_month.strftime(fmt)

            delta = str(datetime.now())

            if delta == compute or delta > compute and item.state in ['draft','in_progress','open']:
                item.validation_due_date = True
        return True

    @api.one
    @api.depends('name','ordering_date','companys_id','type_location')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d'

        if self.name and self.ordering_date and self.companys_id.code and self.type_location:
            date = self.ordering_date
            conv_date = datetime.strptime(str(date), fmt)
            month = conv_date.month
            year = conv_date.year

            #change integer to roman
            if type(month) != type(1):
                raise TypeError, "expected integer, got %s" % type(month)
            if not 0 < month < 4000:
                raise ValueError, "Argument must be between 1 and 3999"
            ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
            nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
            result = ""
            for i in range(len(ints)):
              count = int(month / ints[i])
              result += nums[i] * count
              month -= ints[i] * count
            month = result

            self.complete_name = self.name + '/' \
                                 + self.companys_id.code+' - '\
                                 +'PQ'+'/'\
                                 +str(self.type_location)+'/'+str(month)+'/'+str(year)
        else:
            self.complete_name = self.name

        return True

    def _prepare_po_from_tender(self, cr, uid, tender, context=None):
        """ Prepare the values to write in the purchase order
        created from a tender.

        :param tender: the source tender from which we generate a purchase order
        """
        sequence_name = 'purchase.order.seq.'+tender.type_location.lower()+'.'+tender.companys_id.code.lower()
        return {'order_line': [],
                'requisition_id': tender.id,
                'po_no':self.pool.get('ir.sequence').next_by_code(cr, uid,sequence_name),
                # 'location':tender.location,
                'source_purchase_request' : tender.origin,
                'request_id':tender.request_id.id,
                'companys_id' :tender.companys_id.id,
                'origin': tender.complete_name}

    def _prepare_purchase_backorder(self, cr, uid, requisition, supplier, context=None):
        return {
            'origin': requisition.complete_name,
            'date_order': requisition.date_end or fields.datetime.now(),
            'partner_id': supplier.id,
            'type_location':requisition.type_location,
            'location':requisition.location,
            'currency_id': requisition.company_id and requisition.company_id.currency_id.id,
            'companys_id': requisition.companys_id.id,
            'fiscal_position_id': self.pool.get('account.fiscal.position').get_fiscal_position(cr, uid, supplier.id, context=context),
            'requisition_id': requisition.id,
            'request_id':requisition.request_id.id,
            'notes': requisition.description,
            'picking_type_id': requisition.picking_type_id.id,
            'comparison_id' : requisition.comparison_id,
            'validation_check_backorder':True
        }

    def _prepare_missing_purchase_backorder(self, cr, uid, requisition, supplier, context=None):
        return {
            'origin': requisition.complete_name,
            'date_order': requisition.date_end or fields.datetime.now(),
            'partner_id': supplier.id,
            'type_location':requisition.type_location,
            'location':requisition.location,
            'currency_id': requisition.company_id and requisition.company_id.currency_id.id,
            'companys_id': requisition.companys_id.id,
            'fiscal_position_id': self.pool.get('account.fiscal.position').get_fiscal_position(cr, uid, supplier.id, context=context),
            'requisition_id': requisition.id,
            'request_id':requisition.request_id.id,
            'notes': requisition.description,
            'picking_type_id': requisition.picking_type_id.id,
            'comparison_id' : requisition.comparison_id,
            'validation_check_backorder':False
        }

    def _prepare_purchase_backorder_line(self, cr, uid, requisition, requisition_line, purchase_id, supplier, context=None):
        if context is None:
            context = {}
        po_obj = self.pool.get('purchase.order')
        po_line_obj = self.pool.get('purchase.order.line')
        product_uom = self.pool.get('product.uom')
        product = requisition_line.product_id
        default_uom_po_id = product.uom_po_id.id
        ctx = context.copy()
        ctx['tz'] = requisition.user_id.tz
        date_order = requisition.ordering_date  or fields.datetime.now()
        qty = product_uom._compute_qty(cr, uid, requisition_line.product_uom_id.id, requisition_line.qty_outstanding, default_uom_po_id)

        taxes = product.supplier_taxes_id
        fpos = supplier.property_account_position_id
        taxes_id = fpos.map_tax(taxes).ids if fpos else []

        po = po_obj.browse(cr, uid, [purchase_id], context=context)
        seller = requisition_line.product_id._select_seller(
            requisition_line.product_id,
            partner_id=supplier,
            quantity=qty,
            date=date_order and date_order[:10],
            uom_id=product.uom_po_id)

        price_unit = seller.price if seller else 0.0
        if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
            price_unit = seller.currency_id.compute(price_unit, po.currency_id)

        date_planned = po_line_obj._get_date_planned(cr, uid, seller, po=po, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        product_lang = requisition_line.product_id.with_context({
            'lang': supplier.lang,
            'partner_id': supplier.id,
        })
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        vals = {
            'name': name,
            'order_id': purchase_id,
            'product_qty': qty,
            'qty_request':qty,
            'product_id': product.id,
            'product_uom': default_uom_po_id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'comparison_id' : requisition.comparison_id,
            'trigger_draft' : True,
            'taxes_id': [(6, 0, taxes_id)],
            'account_analytic_id': requisition_line.account_analytic_id.id,
            'validation_check_backorder': po.comparison_id.validation_check_backorder
        }

        return vals

    def _prepare_missing_purchase_backorder_line(self, cr, uid, requisition, requisition_line, purchase_id, supplier, context=None):
        if context is None:
            context = {}
        po_obj = self.pool.get('purchase.order')
        po_line_obj = self.pool.get('purchase.order.line')
        product_uom = self.pool.get('product.uom')
        product = requisition_line.product_id
        default_uom_po_id = product.uom_po_id.id
        ctx = context.copy()
        ctx['tz'] = requisition.user_id.tz
        date_order = requisition.ordering_date  or fields.datetime.now()
        qty = product_uom._compute_qty(cr, uid, requisition_line.product_uom_id.id, requisition_line.product_qty, default_uom_po_id)
        qty1 = product_uom._compute_qty(cr, uid, requisition_line.product_uom_id.id, requisition_line.qty_outstanding, default_uom_po_id)

        taxes = product.supplier_taxes_id
        fpos = supplier.property_account_position_id
        taxes_id = fpos.map_tax(taxes).ids if fpos else []

        po = po_obj.browse(cr, uid, [purchase_id], context=context)
        seller = requisition_line.product_id._select_seller(
            requisition_line.product_id,
            partner_id=supplier,
            quantity=qty,
            date=date_order and date_order[:10],
            uom_id=product.uom_po_id)

        seller2 = requisition_line.product_id._select_seller(
            requisition_line.product_id,
            partner_id=supplier,
            quantity=qty1,
            date=date_order and date_order[:10],
            uom_id=product.uom_po_id)

        price_unit = seller.price if seller else 0.0
        if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
            price_unit = seller.currency_id.compute(price_unit, po.currency_id)

        price_unit2 = seller2.price if seller2 else 0.0
        if price_unit and seller2 and po.currency_id and seller2.currency_id != po.currency_id:
            price_unit = seller2.currency_id.compute(price_unit2, po.currency_id)

        date_planned = po_line_obj._get_date_planned(cr, uid, seller, po=po, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        product_lang = requisition_line.product_id.with_context({
            'lang': supplier.lang,
            'partner_id': supplier.id,
        })
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        vals = {
            'name': name,
            'order_id': purchase_id,
            'product_qty': qty if requisition_line.qty_outstanding == 0 else qty1,
            'qty_request':qty if requisition_line.qty_outstanding == 0 else qty1,
            'product_id': product.id,
            'product_uom': default_uom_po_id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'taxes_id': [(6, 0, taxes_id)],
            'comparison_id' : requisition.comparison_id,
            'trigger_draft' : True,
            'account_analytic_id': requisition_line.account_analytic_id.id,
        }

        return vals


    def make_purchase_backorder(self, cr, uid, ids, partner_id, context=None):
        """
        Create New RFQ for Vendor
        """
        context = dict(context or {})
        assert partner_id, 'Vendor should be specified'
        purchase_order = self.pool.get('purchase.order')
        purchase_order_line = self.pool.get('purchase.order.line')
        res_partner = self.pool.get('res.partner')
        supplier = res_partner.browse(cr, uid, partner_id, context=context)
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            #todo use constraint for vendor.
            if not requisition.multiple_rfq_per_supplier and supplier.id in filter(lambda x: x, [((rfq.validation_check_backorder == True and rfq.state  not in ('cancel')) or (rfq.validation_check_backorder == False and rfq.state in ('draft')))and rfq.partner_id.id or None for rfq in requisition.purchase_ids]):
                error_msg = "You have already one  purchase order for this partner, you must cancel this purchase order to create a new quotation."
                raise exceptions.ValidationError(error_msg)
            context.update({'mail_create_nolog': True})
            if requisition.validation_check_backorder == True:
                purchase_id = purchase_order.create(cr, uid, self._prepare_purchase_backorder(cr, uid, requisition, supplier, context=context), context=context)
            elif requisition.validation_check_backorder == True and requisition.validation_missing_product == True:
                purchase_id = purchase_order.create(cr, uid, self._prepare_missing_purchase_backorder(cr, uid, requisition, supplier, context=context), context=context)
            elif requisition.validation_missing_product == True:
                purchase_id = purchase_order.create(cr, uid, self._prepare_missing_purchase_backorder(cr, uid, requisition, supplier, context=context), context=context)
            else:
                purchase_id = purchase_order.create(cr, uid, self._prepare_missing_purchase_backorder(cr, uid, requisition, supplier, context=context), context=context)
            purchase_order.message_post(cr, uid, [purchase_id], body=_("RFQ created"), context=context)
            res[requisition.id] = purchase_id
            for line in requisition.line_ids:
                if line.qty_outstanding > 0 and line.check_missing_product == False:
                    purchase_order_line.create(cr, uid, self._prepare_purchase_backorder_line(cr, uid, requisition, line, purchase_id, supplier, context=context), context=context)
                elif line.check_missing_product == True :
                    purchase_order_line.create(cr, uid, self._prepare_missing_purchase_backorder_line(cr, uid, requisition, line, purchase_id, supplier, context=context), context=context)
                elif line.check_missing_product == True and line.qty_outstanding > 0:
                    purchase_order_line.create(cr, uid, self._prepare_missing_purchase_backorder_line(cr, uid, requisition, line, purchase_id, supplier, context=context), context=context)
        return res

    def _prepare_purchase_order_line(self, cr, uid, requisition, requisition_line, purchase_id, supplier, context=None):
        if context is None:
            context = {}
        po_obj = self.pool.get('purchase.order')
        po_line_obj = self.pool.get('purchase.order.line')
        product_uom = self.pool.get('product.uom')
        product = requisition_line.product_id
        default_uom_po_id = product.uom_po_id.id
        ctx = context.copy()
        ctx['tz'] = requisition.user_id.tz
        date_order = requisition.ordering_date  or fields.datetime.now()
        requisition_line_qty = requisition_line.qty_outstanding if requisition_line.qty_outstanding > 0 else requisition_line.product_qty
        qty = product_uom._compute_qty(cr, uid, requisition_line.product_uom_id.id, requisition_line_qty, default_uom_po_id)

        taxes = product.supplier_taxes_id
        fpos = supplier.property_account_position_id
        taxes_id = fpos.map_tax(taxes).ids if fpos else []

        po = po_obj.browse(cr, uid, [purchase_id], context=context)
        seller = requisition_line.product_id._select_seller(
            requisition_line.product_id,
            partner_id=supplier,
            quantity=qty,
            date=date_order and date_order[:10],
            uom_id=product.uom_po_id)

        price_unit = seller.price if seller else 0.0
        if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
            price_unit = seller.currency_id.compute(price_unit, po.currency_id)

        date_planned = po_line_obj._get_date_planned(cr, uid, seller, po=po, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        product_lang = requisition_line.product_id.with_context({
            'lang': supplier.lang,
            'partner_id': supplier.id,
        })
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        vals = {
            'name': name,
            'order_id': purchase_id,
            'product_qty': qty,
            'product_id': product.id,
            'product_uom': default_uom_po_id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'taxes_id': [(6, 0, taxes_id)],
            'trigger_draft' : True,
            'account_analytic_id': requisition_line.account_analytic_id.id,
        }

        return vals

    def _prepare_po_line_from_tender(self, cr, uid, tender, line, purchase_id, context=None):
        """ Prepare the values to write in the purchase order line
        created from a line of the tender.

        :param tender: the source tender from which we generate a purchase order
        :param line: the source tender's line from which we generate a line
        :param purchase_id: the id of the new purchase
        """
        return {
                'trigger_draft' : False,
                'product_qty': line.quantity_tendered,
                'order_id': purchase_id
               }

    # @api.multi
    # def generate_po(self):
    #     for item in self:
    #         super(InheritPurchaseTenders,item).generate_po()


    @api.multi
    def set_done(self):
        for item in self:
            # Set To Done Purchase Tender
            pp_data={'state':'done'}
            item.env['purchase.request'].search([('complete_name','like',item.origin)]).write(pp_data)
            item.write({'state' : 'done'})


    @api.multi
    @api.constrains('purchase_ids')
    def _constraint_po_line_ids(self):

        for item in self:

            arrPoid = []
            tender_line =item.env['purchase.requisition.line']
            tender_line_id = tender_line.search([('requisition_id','=',item.id)])
            if item.purchase_ids:
                for record in item.purchase_ids:
                    arrPoid.append(record.id)

                for tender in tender_line_id:

                    order_line_ids = item.env['purchase.order.line'].search([('order_id','in',arrPoid),('product_id','=',tender.product_id.id)])

                    for order in order_line_ids:
                        if order.quantity_tendered > tender.product_qty:
                            error_msg = 'Quantity tendered cannot more than Product Quantity in Tender Line'
                            raise exceptions.ValidationError(error_msg)
                        elif order.product_qty > tender.product_qty:
                            error_msg = 'Product Quantity \"%s\" cannot greater than Product Quantity \"%s\" in Tender Line Vendor \"%s\"'%(order.product_id.name,tender.product_id.name,order.partner_id.name)
                            raise exceptions.ValidationError(error_msg)

    #Email Template Code Starts Here

    @api.one
    def send_mail_template(self):
            # Find the e-mail template
            template = self.env.ref('purchase_indonesia.email_template_correction_purchase_request')
            # You can also find the e-mail template like this:
            # template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
            # Send out the e-mail template to the user
            self.env['mail.template'].browse(template.id).send_mail(self.id,force_send=True)
    
    @api.one
    def send_mail_template_new_tender(self):
            # Find the e-mail template
            # template = self.env.ref('purchase_indonesia.email_template_new_purchase_tender')
            template = self.env.ref('purchase_indonesia.email_template_new_purchase_tender_new')
            # You can also find the e-mail template like this:
            # template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
            # Send out the e-mail template to the user
            self.env['mail.template'].browse(template.id).send_mail(self.id,force_send=True)

    @api.multi
    def database(self):
        for item in self:
            db = item.env.cr.dbname

            return db

    @api.multi
    def web_url(self):
        for item in self:
            web = item.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return web

    @api.multi
    def email_model(self):
        for item in self:
            model = item._name
            return model

class InheritPurchaseRequisitionLine(models.Model):

    _inherit = 'purchase.requisition.line'
    _order = 'product_id asc'

    qty_received = fields.Float('Quantity Received',readonly=True)
    qty_outstanding = fields.Float('Quantity Outstanding',readonly=True)
    check_missing_product = fields.Boolean('Checking Missing Product')
    est_price = fields.Float('Estimated Price',compute='_compute_est_price')
    qty_outstanding_comp = fields.Float('Quantity Outstanding', compute='_compute_qty_outstanding_comp', readonly=True)
    
    @api.multi
    def _compute_qty_outstanding_comp(self):
        for item in self:
            item.qty_outstanding_comp = item.product_qty - item.qty_received
        
    @api.multi
    @api.depends('est_price')
    def _compute_est_price(self):
        if self.est_price == 0 :
            for item in self:
                request_line  = item.env['purchase.request.line'].search([('request_id','=',item.requisition_id.request_id.id),
                                                                          ('product_id','=',item.product_id.id)]).price_per_product
                item.est_price = request_line

class TriggerPurchaseTender(models.Model):
    _name = "purchase.requisition.trigger"
    _description = "trigger to change status PO, GRN and Invoice on tender"
    _auto = False
    
    def init(self, cr):
        cr.execute("""
            create or replace function public.t_quotation_tender() returns trigger 
            LANGUAGE plpgsql
            as $function$
                declare
                    v_is_qcf_done boolean;
                begin 
                    select case when count(*) = cast(0 as bigint) then true else false end delta from (
                        select request_id, product_id, control_unit product_qty from purchase_request_line where request_id = NEW.request_id 
                        except
                        select 
                            po.request_id, pol.product_id,pol.product_qty from (
                            select 
                                * 
                            from 
                                purchase_order 
                            where 
                                request_id = NEW.request_id 
                                and state not in ('purchase','done','received_all','received_force_done')
                            )po inner join purchase_order_line pol on po.id = pol.order_id
                    )po_tender into v_is_qcf_done;
                    
                    update purchase_requisition 
                        set is_qcf_done = v_is_qcf_done
                    where request_id = NEW.request_id; 
                    
                    RETURN NEW;
                end; 
            $function$
        """)
        
        cr.execute("""
            create or replace function public.t_purchase_order_tender() returns trigger 
            LANGUAGE plpgsql
            as $function$
                declare
                    v_is_po_done boolean;
                begin 
                    select case when count(*) = cast(0 as bigint) then true else false end delta from (
                        select request_id, product_id, control_unit product_qty from purchase_request_line where request_id = NEW.request_id 
                        except
                        select 
                            po.request_id, pol.product_id,sum(pol.product_qty) product_qty from (
                            select 
                                * 
                            from 
                                purchase_order 
                            where 
                                request_id = NEW.request_id 
                                and state in ('purchase','done','received_all','received_force_done')
                            )po inner join purchase_order_line pol on po.id = pol.order_id
                            group by
                                po.request_id, pol.product_id
                    )po_tender into v_is_po_done;
                    
                    update purchase_requisition 
                        set is_po_done = v_is_po_done
                    where request_id = NEW.request_id; 
                    
                    RETURN NEW;
                end; 
            $function$
        """)
        
        cr.execute("""
            create or replace function public.t_grn_tender() returns trigger 
            LANGUAGE plpgsql
            as $function$
                declare
                    v_is_grn_done boolean;
                begin 
                    select case when count(*) = cast(0 as bigint) then true else false end delta from (            
                        select 
                            request_id, product_id, control_unit product_qty from purchase_request_line 
                        where 
                            request_id in (select request_id from purchase_order where name = NEW.origin) 
                        except
                        select 
                            po.request_id, spo.product_id,sum(spo.product_qty) product_qty from (
                            select 
                                * 
                            from 
                                purchase_order 
                            where 
                                request_id in (select request_id from purchase_order where name = NEW.origin) 
                                and state in ('purchase','done')
                            )po inner join stock_picking sp on po.name = sp.origin 
                            inner join stock_pack_operation spo on sp.id = spo.picking_id
                            where 
                                sp.state = 'done' and spo.checking_split != true
                            group by
                                po.request_id, spo.product_id
                    )po_tender into v_is_grn_done;
                    
                    update purchase_requisition 
                        set is_grn_done = v_is_grn_done
                    where request_id in (select request_id from purchase_order where name = NEW.origin); 
                    
                    RETURN NEW;
                end; 
            $function$
        """)
        
        cr.execute("""
            create or replace function public.t_inv_tender() returns trigger 
            LANGUAGE plpgsql
            as $function$
                declare
                    v_is_inv_done boolean;
                begin 
                    select case when count(*) = cast(0 as bigint) then true else false end delta from (
                        select 
                            request_id, product_id, control_unit product_qty 
                        from 
                            purchase_request_line 
                        where 
                            request_id in (select request_id from purchase_order where name = NEW.origin) 
                        except
                        select 
                            po.request_id, ail.product_id,sum(ail.quantity) product_qty from (
                            select 
                                * 
                            from 
                                purchase_order 
                            where 
                                request_id in (select request_id from purchase_order where name = NEW.origin) 
                                and state in ('purchase','done')
                            )po 
                            inner join account_invoice ai on ai.origin = po.name
                            inner join account_invoice_line ail on ai.id = ail.invoice_id
                            where ai.state in ('open','paid')
                            group by 
                                po.request_id, ail.product_id
                    )po_tender into v_is_inv_done;
                    
                    update purchase_requisition 
                        set is_inv_done = v_is_inv_done
                    where request_id in (select request_id from purchase_order where name = NEW.origin); 
                    
                    RETURN NEW;
                end; 
            $function$
        """)
        
        try:
            cr.execute("""
                CREATE TRIGGER t_quotation_tender_ins 
                    AFTER INSERT ON 
                        purchase_order FOR EACH ROW EXECUTE PROCEDURE t_quotation_tender();
                COMMIT;
            """)
        except:
            print "Please check trigger in database : t_quotation_tender_ins on purchase_order" 
             
        try:
            cr.execute("""
                CREATE TRIGGER t_quotation_tender_upd
                    AFTER UPDATE OF validation_check_confirm_vendor ON 
                        purchase_order FOR EACH ROW EXECUTE PROCEDURE t_quotation_tender();
                COMMIT;
            """)
        except:
            print "Please check trigger in database : t_quotation_tender_upd on purchase_order" 
          
        try:
            cr.execute("""
                CREATE TRIGGER t_purchase_order_tender_ins 
                    AFTER INSERT ON 
                        purchase_order FOR EACH ROW EXECUTE PROCEDURE t_purchase_order_tender();
                COMMIT;
            """)
        except:
            print "Please check trigger in database : t_purchase_order_tender_ins on purchase_order" 
              
        try:    
            cr.execute("""
                CREATE TRIGGER t_purchase_order_tender_upd 
                    AFTER UPDATE OF state ON 
                        purchase_order FOR EACH ROW EXECUTE PROCEDURE t_purchase_order_tender();
                COMMIT;
            """)
        except:
            print "Please check trigger in database : t_purchase_order_tender_upd on purchase_order" 
              
        try:    
            cr.execute("""
                CREATE TRIGGER t_grn_tender_upd 
                    AFTER UPDATE ON 
                        stock_picking FOR EACH ROW EXECUTE PROCEDURE t_grn_tender();
                COMMIT;
            """)
        except:
            print "Please check trigger in database : t_grn_tender_upd on stock_picking" 
              
        try:    
            cr.execute("""
                CREATE TRIGGER t_inv_tender_upd 
                    AFTER UPDATE OF state ON 
                        account_invoice FOR EACH ROW EXECUTE PROCEDURE t_inv_tender();
                COMMIT;
            """)
        except:
            print "Please check trigger in database : t_inv_tender_upd on account_invoice"
            
# class InheritPurchaseOrderTender(models.Model):
# 
#     _inherit = 'purchase.order'
#     
#     @api.multi
#     @api.onchange('validation_check_confirm_vendor')
#     def _onchange_validation_check_confirm_vendor(self):
#         print '_onchange_validation_check_confirm_vendor'
#         for item in self:
#             prs = item.env['purchase.requisition'].search([('request_id','=',item.request_id.id)])
#             for pr in prs:
#                 pr.set_status_po_grn_inv()

class SummaryProgressPurchaseRequest(models.Model):
    _name = 'v.summary.progress.pp.report'
    _description = 'Summary Progress Purchase Request'
    _auto = False
    
    company_name = fields.Char("1")
    category_name  = fields.Char("2")
    ho  = fields.Char("3")
    ro  = fields.Char("4")
    po_done  = fields.Char("5")
    po_undone  = fields.Char("6")
    
    def init(self, cr):
        drop_view_if_exists(cr, 'v_summary_progress_pp_report')
        drop_view_if_exists(cr, 'v_summary_progress_pp_undone_current')
        drop_view_if_exists(cr, 'v_summary_progress_pp_current')
        drop_view_if_exists(cr, 'v_summary_progress_pp')
        
        cr.execute("""
            create or replace view v_summary_progress_pp as
                select
                    pr.company_name,
                    pr.code,
                    (case when pr.category_name is null then 'Confirmation' else pr.category_name end) category_name,
                    po_summary.*,
                    date_part('month',po_summary.pr_create_date) pr_month,
                    date_part('year',po_summary.pr_create_date) pr_year,
                    date_part('month',po_summary.po_create_date) po_month,
                    date_part('year',po_summary.po_create_date) po_year
                from 
                (
                    (
                        select
                            pr.request_id,
                            (case when pr.is_qcf_done is null then false else pr.is_qcf_done end) is_qcf_done,
                            (case when pr.is_spec_not_clear is null then false else pr.is_spec_not_clear end) is_spec_not_clear,
                            pr.create_date pr_create_date,
                            po.create_date po_create_date,
                            'po_done' state
                        from 
                            (select requisition_id, max(create_date) create_date from purchase_order group by requisition_id) po 
                            right join 
                            (select * from purchase_requisition where is_po_done = true) pr
                            on po.requisition_id = pr.id
                    )
                    union all
                    (
                        select 
                            pr.request_id,
                            (case when pr.is_qcf_done is null then false else pr.is_qcf_done end) is_qcf_done,
                            (case when pr.is_spec_not_clear is null then false else pr.is_spec_not_clear end) is_spec_not_clear,
                            pr.create_date pr_create_date,
                            po.create_date po_create_date,
                            'po_undone' state
                        from 
                            (select requisition_id, max(create_date) create_date from purchase_order group by requisition_id) po 
                            right join 
                            (select * from purchase_requisition where is_po_done = false or is_po_done is null) pr
                            on po.requisition_id = pr.id    
                    )
                )po_summary 
                inner join 
                (    select 
                        pr.id,
                        rc.name company_name,
                        pit.name category_name,
                        (case when pr.code = 'KOKB' then 'RO' else 'HO' end) code
                    from 
                        (    
                            select 
                                id,
                                company_id,
                                code,
                                (case when is_confirmation is true then 0 else type_purchase end) type_purchase 
                            from 
                                purchase_request 
                            where 
                                active = true
                        ) pr 
                        inner join 
                        res_company rc on rc.id = pr.company_id
                        left join 
                        purchase_indonesia_type pit
                        on pr.type_purchase = pit.id
                ) pr 
                on po_summary.request_id = pr.id
        """)
        
        cr.execute("""
            create or replace view v_summary_progress_pp_current as
            with param_month as (
                select 
                    case when (select "value"::integer val from ir_config_parameter where key = 'summary_progress_pp_month_param') is null 
                    then date_part('month', now()) else 
                    (select "value"::integer val from ir_config_parameter where key = 'summary_progress_pp_month_param')
                    end
            ),
            param_year as (
                select 
                    case when (select "value"::integer val from ir_config_parameter where key = 'summary_progress_pp_year_param') is null 
                    then date_part('year', now()) else 
                    (select "value"::integer val from ir_config_parameter where key = 'summary_progress_pp_year_param')
                    end 
            )
            select 
                    dummy.company_name_val company_name,
                    dummy.category_name,
                    ''||summ.ho ho,
                    ''||summ.ro ro,
                    ''||summ.po_done po_done,
                    ''||summ.po_undone po_undone,
                    summ.ho ho_val,
                    summ.ro ro_val,
                    summ.po_done po_done_val,
                    summ.po_undone po_undone_val
                from 
                (
                    select 
                        case when category_name in ('Urgent','Confirmation') then '' else company_name end company_name_val,
                        company_name,
                        category_name,
                        id
                    from (
                        select name company_name from res_company where code != 'PG'
                        ) rc, 
                        (
                            select id, name category_name from purchase_indonesia_type
                            union all
                            select (select max(id)+1 from purchase_indonesia_type)id, 'Confirmation' category_name
                        ) pit
                ) dummy
                left join 
                (
                    select  
                        by_code.company_name,
                        by_code.category_name,
                        by_code.ho,
                        by_code.ro,
                        by_state.po_done,
                        by_state.po_undone
                    from 
                    (
                        select 
                            summ.company_name, 
                            summ.category_name,
                            sum(
                                CASE WHEN
                                 code = 'RO' THEN summ.total_code
                                ELSE (0)::numeric
                            END) AS RO,
                            sum(
                                CASE WHEN
                                 code = 'HO' THEN summ.total_code
                                ELSE (0)::numeric
                            END) AS HO
                        from 
                        (
                            select company_name, category_name, code, count(*) total_code from (
                                select * from v_summary_progress_pp where 
                                    (
                                        pr_month = (select val from param_month)
                                        and 
                                        pr_year = (select val from param_year)
                                    ) or
                                    (    
                                        pr_month < (select val from param_month)
                                        and 
                                        pr_year = (select val from param_year)
                                    )
                            ) summ group by company_name, category_name, code
                        )summ group by company_name, category_name
                    ) by_code 
                    inner join 
                    (
                        select 
                            summ.company_name, 
                            summ.category_name,
                            sum(
                                CASE WHEN
                                 state = 'po_undone' THEN summ.total_state
                                ELSE (0)::numeric
                            END) AS po_undone,
                            sum(
                                CASE WHEN
                                 state = 'po_done' THEN summ.total_state
                                ELSE (0)::numeric
                            END) AS po_done
                        from 
                        (
                            select company_name, category_name, state, count(*) total_state from (
                                select * from v_summary_progress_pp where 
                                    (pr_month = (select val from param_month)  and pr_year = (select val from param_year) ) or
                                    (pr_month < (select val from param_month)  and pr_year = (select val from param_year)  and state = 'po_undone')
                            ) summ group by company_name, category_name, state
                        )summ group by company_name, category_name
                    ) by_state on by_code.company_name = by_state.company_name and by_code.category_name = by_state.category_name
                )summ on dummy.company_name = summ.company_name and dummy.category_name = summ.category_name;
        """)
        
        cr.execute("""
            create or replace view v_summary_progress_pp_undone_current as
                with param_month as (
                    select 
                        case when (select "value"::integer val from ir_config_parameter where key = 'summary_progress_pp_month_param') is null 
                        then date_part('month', now()) else 
                        (select "value"::integer val from ir_config_parameter where key = 'summary_progress_pp_month_param')
                        end
                ),
                param_year as (
                    select 
                        case when (select "value"::integer val from ir_config_parameter where key = 'summary_progress_pp_year_param') is null 
                        then date_part('year', now()) else 
                        (select "value"::integer val from ir_config_parameter where key = 'summary_progress_pp_year_param')
                        end 
                )
                select 
                    row_number() over () idx,
                    dummy.status_pp_undone,
                    (case when data_value.total is null then 0 else data_value.total end) total
                from (
                    select 'Proses Quotation' status_pp_undone
                    union all
                    select 'Proses Approval PO' status_pp_undone
                    union all
                    select 'PP Bertahap' status_pp_undone
                    union all
                    select 'Spesifikasi Belum Jelas' status_pp_undone
                ) dummy left join 
                (    
                    select 
                        status_pp_undone,
                        sum(total) as total
                    from (
                        select
                            (case when is_qcf_done = true then 'Proses Approval PO' else 
                                (case when is_spec_not_clear = true then 'Spesifikasi Belum Jelas' else 
                                    (case when po_month is not null then 'PP Bertahap' else 'Proses Quotation' end)
                                end)  
                            end) as status_pp_undone,
                            count(*) total
                        from 
                            v_summary_progress_pp 
                        where 
                            ((pr_month = (select val from param_month) and pr_year = (select val from param_year)) or
                            (pr_month < (select val from param_month) and pr_year = (select val from param_year))) and
                            state = 'po_undone'
                        group by 
                            is_qcf_done,is_spec_not_clear,po_month
                    )a group by status_pp_undone
                ) data_value 
                on dummy.status_pp_undone = data_value.status_pp_undone;
        """)
        
        cr.execute("""
            create or replace view v_summary_progress_pp_report as
                with param_month as (
                    select 
                        case when (select "value"::integer val from ir_config_parameter where key = 'summary_progress_pp_month_param') is null 
                        then date_part('month', now()) else 
                        (select "value"::integer val from ir_config_parameter where key = 'summary_progress_pp_month_param')
                        end
                ),
                param_year as (
                    select 
                        case when (select "value"::integer val from ir_config_parameter where key = 'summary_progress_pp_year_param') is null 
                        then date_part('year', now()) else 
                        (select "value"::integer val from ir_config_parameter where key = 'summary_progress_pp_year_param')
                        end 
                )
                select 
                    row_number() over() id,
                    summ.* 
                from 
                (
                    select '' company_name, '' category_name, 'PP s.d Bulan '|| (select val from param_month) || ' Tahun ' || (select val from param_year) ho, null ro, 'PP Final Process' po_done, 'PP on Process' po_undone
                    union all
                    select 'Perusahaan' company_name, 'Kategori' category_name, 'HO' ho, 'SO' ro, '(Done)' po_done, '(Undone)' po_undone
                    union all
                    select company_name, category_name, ho, ro, po_done, po_undone from v_summary_progress_pp_current
                    union all
                    select '' company_name, 'Total' category_name, null ho, ''||sum(ho_val)+sum(ro_val) ro, ''||sum(po_done_val) po_done, ''||sum(po_undone_val) po_undone from v_summary_progress_pp_current
                    union all
                    select '' company_name, '' category_name, null ho, null ro, null po_done, null po_undone
                    union all
                    select 'No' company_name, 'Status PP Undone' category_name, 'Jumlah PP' ho, null ro, null po_done, null po_undone
                    union all
                    select ''||idx company_name,status_pp_undone category_name, ''||total ho, null ro, null po_done, null po_undone from v_summary_progress_pp_undone_current
                    union all
                    select null company_name,'Total' category_name, ''||sum(total) ho, null ro, null po_done, null po_undone from v_summary_progress_pp_undone_current
                ) summ; 
        """)
    
class ViewPurchaseTenderLine(models.Model):
    _name = 'v.purchase.requisition.line'
    _description = 'Purchase Request Line'
    _auto = False
    
    request_id = fields.Many2one('purchase.request','Purchase Request')
    product_id = fields.Many2one('product.product', 'Product')
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure')
    company_id = fields.Many2one('res.company', 'Company')
    product_qty = fields.Float('Quantity')
    qty_received = fields.Float('Quantity Received')
    qty_outstanding = fields.Float('Quantity Outstanding')
    ordering_date = fields.Date('Ordering Date')
    is_qcf_done = fields.Boolean('QCF Done')
    is_po_done = fields.Boolean('PO Done')
    is_grn_done = fields.Boolean('GRN Done')
    is_inv_done = fields.Boolean('Invoice Done')
    pic = fields.Many2one('res.users', 'PIC')
    qcf_id = fields.Char('QCF')
    po_id = fields.Char('Purchase Order')
    po_approve_date = fields.Date('PO Approve Date')
    price_unit = fields.Float('Unit Price')
    price_tax = fields.Float('Tax')
    price_subtotal = fields.Float('Subtotal')
    partner_id = fields.Many2one('res.partner','Vendor')
    grn_id = fields.Char('GRN')
    completion_date = fields.Date('Completion Date')
    create_date = fields.Date('PP Create Date')
    approve_date = fields.Date('PP Approve Date')
    category = fields.Char('PP Category')
    status = fields.Char('Status')
    pr_state = fields.Selection([('draft', 'Draft'), 
                                 ('in_progress', 'Confirmed'),
                                 ('open', 'Bid Selection'), 
                                 ('rollback','Roll Back PP'),
                                 ('closed','PP Closed'),
                                 ('open', 'PP Outstanding'),
                                 ('done', 'Shipment'),
                                 ('cancel', 'Cancelled')]
                                )
    requested_by = fields.Many2one('res.users','Requested by')
    department_id = fields.Many2one('hr.department','Department')
    
    def init(self, cr):
        drop_view_if_exists(cr, 'v_purchase_requisition')
        drop_view_if_exists(cr, 'v_purchase_requisition_line')
        
        cr.execute("""
            create or replace view v_purchase_requisition_line
            as
            select
                row_number() over() id,
                pr.requisition_id,
                pr.request_id,
                pr.requested_by,
                pr.department_id,
                pr.create_date::date create_date,
                pr.approve_date::date approve_date,
                pr.category,
                pr.product_id,
                pr.product_uom_id,
                pr.company_id,
                --pr.product_qty,
                --pr.qty_received,
                --pr.qty_outstanding,
                (case when grn.grn_id is null then pr.product_qty else (case when grn.initial_qty is null then grn.product_qty else grn.initial_qty end)end)::numeric  product_qty,
                grn.qty_done::double precision qty_received,
                ((case when grn.initial_qty is null then grn.product_qty else grn.initial_qty end) - grn.qty_done)::double precision qty_outstanding,
                pr.ordering_date::date ordering_date,
                pr.is_qcf_done,
                pr.is_grn_done,
                pr.is_inv_done,
                (case when po.po_id is not null or pr.state = 'cancel' then true else false end) is_po_done,
                pr.pic,
                qcf.qcf_id,
                po.po_id,
                po.origin,
                po.po_approve_date::date po_approve_date,
                po.price_unit,
                po.price_tax,
                po.price_subtotal,
                po.partner_id,
                grn.grn_id,
                grn.completion_date::date completion_date,
                (case when is_inv_done = true then '5-Invoice Done' else 
                    (case when is_grn_done = true then '4-GRN Done' else
                        (case when is_po_done = true then '3-PO Done' else
                            (case when is_qcf_done = true then '2-QCF Done' else
                                 '1-PP Full Approved'
                            end)
                        end) 
                    end)
                end) status,
                pr.state pr_state
            from 
                (
                    select
                        prl.requisition_id,
                        pr.request_id,
                        pr.requested_by,
                        pr.department_id,
                        pr.create_date,
                        pr.approve_date,
                        pr.category,
                        prl.product_id,
                        prl.product_uom_id,
                        pr.companys_id company_id,
                        prl.product_qty,
                        (case when prl.qty_received is null then 0.0 else prl.qty_received end) qty_received,
                        (prl.product_qty - (case when prl.qty_received is null then 0.0 else prl.qty_received end)) qty_outstanding,
                        pr.ordering_date,
                        pr.is_qcf_done,
                        pr.is_grn_done,
                        pr.is_po_done,
                        pr.is_inv_done,
                        pr.pic,
                        pr.state
                    from 
                        purchase_requisition_line prl inner join 
                        (select 
                            preq.id,
                            pr.create_date,
                            pr.requested_by,
                            pr.department_id,
                            preq.create_date approve_date,
                            (case when is_confirmation = true then 'Confirmation' else 
                                (case when pr.type_purchase = 1 then 'Normal' else 'Urgent' end)
                            end) category,
                            pr.id request_id,
                            preq.companys_id,
                            preq.ordering_date,
                            preq.is_qcf_done,
                            preq.is_grn_done,
                            preq.is_inv_done,
                            preq.is_po_done,
                            preq.user_id pic,
                            preq.state
                            from 
                                purchase_request pr 
                                inner join purchase_requisition preq 
                                on pr.id = preq.request_id 
                                where pr.active = true
                        ) pr 
                        on prl.requisition_id = pr.id
                ) pr 
                left join 
                (
                    select 
                        max(complete_name) qcf_id, 
                        requisition_id 
                    from 
                        quotation_comparison_form 
                    group by 
                        requisition_id
                ) qcf
                on pr.requisition_id = qcf.requisition_id
                left join 
                (   
                    select
                        po.complete_name po_id,
                        max(po.name) origin,
                        po.requisition_id,
                        max(po.create_date) po_approve_date,
                        pol.product_id,
                        max(pol.price_unit) price_unit,
                        max(pol.price_tax) price_tax,
                        max(pol.price_subtotal) price_subtotal,
                        pol.partner_id
                       from 
                        purchase_order_line pol inner join 
                        (select * from purchase_order where state in ('done','purchase','received_force_done')) po
                        on pol.order_id = po.id
                    group by
                        po.complete_name,po.requisition_id,pol.product_id,pol.partner_id
                 ) po 
                on pr.requisition_id = po.requisition_id and pr.product_id = po.product_id
                left join 
                (
                    select 
                         sp.complete_name_picking grn_id,
                         spo.product_id,
                         spo.qty_done,
                         spo.procurment_qty,
                         spo.initial_qty,
                         spo.product_qty,
                         sp.origin,
                         sp.state,
                         case when sp.state = 'done' then sp.write_date else null end completion_date
                    from 
                         stock_pack_operation spo 
                         inner join stock_picking sp
                         on spo.picking_id = sp.id
                    where
                         product_qty > 0
                )grn
                on grn.product_id = po.product_id and grn.origin = po.origin;
        """)
        
        cr.execute("""
            create or replace view v_purchase_requisition
            as
            select
                row_number() over() id,
                request_id,
                max(create_date)::date create_date,
                max(approve_date)::date approve_date,
                max(category) category,
                max(product_id) product_id,    
                max(company_id) company_id,    
                max(ordering_date)::date ordering_date,    
                case when (max(case when is_qcf_done = true then 1 else 0 end)) = 1 then true else false end is_qcf_done,    
                case when (max(case when is_grn_done = true then 1 else 0 end)) = 1 then true else false end is_grn_done,    
                case when (max(case when is_inv_done = true then 1 else 0 end)) = 1 then true else false end is_inv_done,    
                case when (max(case when is_po_done = true then 1 else 0 end)) = 1 then true else false end is_po_done,    
                max(pic) pic,    
                max(qcf_id) qcf_id,    
                max(po_id) po_id,    
                max(po_approve_date)::date po_approve_date,    
                max(grn_id) grn_id,    
                max(completion_date)::date completion_date,
                max(status) status,
                max(pr_state) pr_state
            from 
                v_purchase_requisition_line 
            group by
                request_id;
        """)
        
class ViewPurchaseTender(models.Model):
    _name = 'v.purchase.requisition'
    _description = 'Purchase Request'
    _auto = False
    
    request_id = fields.Many2one('purchase.request','Purchase Request')
    company_id = fields.Many2one('res.company', 'Company')
    ordering_date = fields.Date('Ordering Date')
    is_qcf_done = fields.Boolean('QCF Done')
    is_po_done = fields.Boolean('PO Done')
    is_grn_done = fields.Boolean('GRN Done')
    is_inv_done = fields.Boolean('Invoice Done')
    pic = fields.Many2one('res.users', 'PIC')
    qcf_id = fields.Char('QCF')
    po_id = fields.Char('Purchase Order')
    po_approve_date = fields.Date('PO Approve Date')
    grn_id = fields.Char('GRN')
    completion_date = fields.Date('Completion Date')
    create_date = fields.Date('PP Create Date')
    approve_date = fields.Date('PP Approve Date')
    category = fields.Char('PP Category')
    status = fields.Char('Status')
    pr_state = fields.Selection([('draft', 'Draft'), 
                                 ('in_progress', 'Confirmed'),
                                 ('open', 'Bid Selection'), 
                                 ('rollback','Roll Back PP'),
                                 ('closed','PP Closed'),
                                 ('open', 'PP Outstanding'),
                                 ('done', 'Shipment'),
                                 ('cancel', 'Cancelled')],
                                'Tender Status')


class VPurchaseOrder(models.Model):
    _name = 'v.purchase.order'
    _description = 'Purchase Order'
    _auto = False

    requested_by = fields.Many2one('res.users','Requested by')
    department_id = fields.Many2one('hr.department','Department')
    create_date = fields.Date('PP Create Date')
    approve_date = fields.Date('PP Approve Date')
    request_id = fields.Char('Purchase Request')
    company_id = fields.Many2one('res.company', 'Company')
    category = fields.Char('PP Category')
    pic_preq = fields.Many2one('res.users', 'PIC')
    qcf_id = fields.Char('QCF')
    pic_po = fields.Many2one('res.users', 'PIC PO')
    po_id = fields.Char('Purchase Order')
    partner_id = fields.Many2one('res.partner','Vendor')

    def init(self, cr):
        drop_view_if_exists(cr, 'v_purchase_order')

        cr.execute("""
            create or replace view v_purchase_order
            as
            select
                row_number() over() id,
                pr.requested_by,
                pr.department_id,
                pr.create_date::date create_date,
                pr.approve_date::date approve_date,
                pr.request_id,
                pr.company_id,
                pr.category,
                pr.user_id pic_preq,
                qcf.complete_name qcf_id,
                qcf.pic_id pic_po,
                po.complete_name po_id,
                po.partner_id
            from
                (
                    select
                        po.complete_name,
                        po.partner_id,
                        po.state,
                        po.comparison_id,
                        po.request_id
                    from
                        purchase_order po
                    where
                        po.state != 'draft'
                        and po.state !=  'cancel'
                ) po
            inner join
                quotation_comparison_form qcf
                on
                qcf.id = po.comparison_id
            inner join
                (
                    select 
                        pr.id,
                        pr.complete_name  request_id,
                        pr.requested_by,
                        pr.department_id,
                        pr.create_date,
                        preq.create_date approve_date,
                        pr.company_id,
                        (case when is_confirmation = true then 'Confirmation' else
                            (case when pr.type_purchase = 1 then 'Normal' else 'Urgent' end)
                        end) category,
                        preq.user_id
                    from
                        purchase_request pr
                    inner join
                        purchase_requisition preq
                        on pr.id = preq.request_id
                    where
                        pr.active = true
                ) pr
                on
                pr.id = po.request_id
            ;
        """)