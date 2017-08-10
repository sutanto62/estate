from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re

class InheritPurchaseOrder(models.Model):

    _inherit = 'purchase.order'
    _rec_name = 'complete_name'

    delivery_term = fields.Selection([('indent','Indent'),('ready','Ready Stock')],'Term Of Delivery')
    days = fields.Float('Days Of Indent')
    companys_id = fields.Many2one('res.company','Company')
    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    type_location = fields.Char('Location')
    location = fields.Char('Location')
    source_purchase_request = fields.Char('Source Purchase Request')
    request_id = fields.Many2one('purchase.request','Purchase Request')
    po_no = fields.Char('Purchase order number')
    hide = fields.Boolean('Hide')
    confirmed_by = fields.Selection([
        ('fax', 'Fax'),
        ('email', 'E-Mail'),
        ('phone', 'Phone'),
        ('other','Other')],store=True)
    confirmed_by_value = fields.Char('Confirmed ByValue',store=True)
    confirmed_by_person = fields.Char('Confirmed ByPerson',store=True)
    validation_confirmed_by = fields.Boolean('Validation Confirmed By',default = False,compute='change_validation_confirmed_by')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),('received_all','Received All'),('received_force_done','Received Partial')
        ], string='Status', readonly=True, select=True, copy=False, default='draft', track_visibility='onchange')
    count_grn_done = fields.Integer('Count GRN Done', compute='_compute_grn_or_srn')
    count_grn_assigned = fields.Integer('Count GRN Assigned', compute='_compute_grn_or_srn')
    count_grn_assigned_user = fields.Integer('Count GRN Assigned', compute='_compute_grn_or_srn')
    validation_check_confirm_vendor = fields.Boolean('Confirm Vendor')
    validation_check_backorder = fields.Boolean('Confirm backorder')

    _defaults = {
        'hide' : False
    }

    @api.multi
    def button_confirm(self):
        self._constraint_quantity_backorder_po()
        self._update_po_no()
        super(InheritPurchaseOrder,self).button_confirm()
        self._update_shipping()
        self._update_delivery_term()
        return True

    @api.multi
    @api.depends('confirmed_by')
    def change_validation_confirmed_by(self):
        for item in self:
            if item.confirmed_by:
                item.validation_confirmed_by = True

    # @api.multi
    # @api.depends('state')
    # def _compute_check_backorder(self):
    #     for item in self:
    #         if item.state in ['cancel','done','purchase','received_all','received_force_done']:
    #             item.validation_check_backorder = True
    #         else:
    #             item.validation_check_backorder = False

    @api.multi
    @api.depends('picking_ids')
    def _compute_grn_or_srn(self):
        for item in self:
            request_name = item.request_id.complete_name
            arrPickingDone = []
            arrPickingAssigned = []
            arrPickingAssignedManager = []
            done = item.env['stock.picking'].search([('purchase_id','=',item.id),('state','=','done')])
            assigned = item.env['stock.picking'].search([('purchase_id','=',item.id),('validation_manager','=',True),('state','=','assigned')])
            assigned_user = item.env['stock.picking'].search([('purchase_id','=',item.id),('validation_user','=',True),('state','=','assigned')])
            for itemDone in done:
                arrPickingDone.append(itemDone.id)
            for itemAssign in assigned:
                arrPickingAssignedManager.append(itemAssign.id)
            for itemAssign1 in assigned_user:
                arrPickingAssigned.append(itemAssign1.id)

            assign_picking_done = item.env['stock.picking'].search([('id','in',arrPickingDone)])
            assign_picking_assigned = item.env['stock.picking'].search([('id','in',arrPickingAssigned)])
            assign_picking_assigned_manager = item.env['stock.picking'].search([('id','in',arrPickingAssignedManager)])

            picking_done = len(assign_picking_done)
            picking_assigned = len(assign_picking_assigned)
            picking_assigned_manager = len(assign_picking_assigned_manager)

            item.count_grn_done = picking_done

            item.count_grn_assigned_user = picking_assigned

            item.count_grn_assigned = picking_assigned_manager

    @api.one
    @api.depends('po_no','name','date_order','companys_id','type_location')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d %H:%M:%S'
        if self.date_order and self.companys_id.code and self.type_location:
            date = self.date_order
            conv_date = datetime.strptime(str(date), fmt)
            month = conv_date.month
            year = conv_date.year
            location = self.type_location

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
            po_no = ''
            if not self.po_no:
                self.complete_name = ' Draft '+self.name  + '/' \
                                 +str(month) +'/'+str(year)\
                                 +'/'+self.companys_id.code+'/'+str(self.type_location)
            elif self.po_no:
                self.complete_name = self.po_no + '/' \
                                 +str(month) +'/'+str(year)\
                                 +'/'+self.companys_id.code+'/'\
                                 +str(self.type_location)

    @api.multi
    def print_quotation(self):
        self.write({'state': "sent"})
        return self.env['report'].get_action(self, 'purchase_indonesia.report_purchase_quotation')

    @api.multi
    def print_purchase_order(self):
        return self.env['report'].get_action(self, 'purchase_indonesia.report_purchase_order')

    @api.multi
    def _update_po_no(self):
        po = self.env['purchase.order'].search([('id','=',self.id)])
        sequence_name = 'purchase.order.seq.'+self.type_location.lower()+'.'+self.companys_id.code.lower()
        purchase_data = {
            'po_no' : self.env['ir.sequence'].next_by_code(sequence_name)
        }
        po.write(purchase_data)

    @api.multi
    def _update_shipping(self):
        #update data in stock.picking
        #return : companys_id,purchase_id,type_location.pr_source
        for purchase_order in self:
            sequence_name = 'stock.grn.seq.'+self.type_location.lower()+'.'+self.companys_id.code.lower()
            purchase_data = {
                'companys_id': purchase_order.companys_id.id,
                'purchase_id': purchase_order.id,
                'type_location': purchase_order.type_location,
                'location':purchase_order.location,
                'pr_source' :purchase_order.request_id.complete_name,
                'grn_no' : self.env['ir.sequence'].next_by_code(sequence_name)
            }
            self.env['stock.picking'].search([('purchase_id','=',self.id)]).write(purchase_data)
        return True

    @api.multi
    def _constraint_quantity_backorder_po(self):

        #search Purchase Tender
        requisition_id = self.env['purchase.requisition'].search([('request_id','=',self.request_id.id)]).id
        for item in self:
            if item.state == 'draft':

                for record in item.order_line:
                    requisition_line_id = self.env['purchase.requisition.line'].search([('requisition_id','=',requisition_id),
                                                                          ('product_id','=',record.product_id.id)])
                    order_line = self.env['purchase.order.line'].search([('order_id','=',self.id),
                                                                         ('product_id','=',requisition_line_id.product_id.id)]).product_qty
                    if requisition_line_id.qty_outstanding > 0 :
                        if order_line > requisition_line_id.qty_outstanding :
                            error_msg = 'Cannot Approve Back Order Cause Product Qty Is more Than Qty Outstanding'
                            raise exceptions.ValidationError(error_msg)

    @api.multi
    def _update_delivery_term(self):
        idx_ready = self.env['purchase.order.line'].search([('order_id','=',self.id),('term_of_goods','=','ready')])
        idx_indent = self.env['purchase.order.line'].search([('order_id','=',self.id),('term_of_goods','=','indent')])
        delivery_data = {
            'delivery_term' : 'ready' if len(idx_ready) >= 1 and len(idx_indent) < 1 or len(idx_ready) >= 1 and len(idx_indent) >= 1 else 'indent'
        }
        self.env['purchase.order'].search([('id','=',self.id)]).write(delivery_data)
        
    def get_employee_job(self,partner_id):
        user = self.env['res.users'].search([('partner_id','=',partner_id)])
        employee = self.env['hr.employee'].search([('user_id','=',user.id)])
        return employee.job_id.name
    
    def _get_price_mid(self):
        #get middle price from purchase params for Purchase Request
        arrMid = []
        try:
            price_standard = self.env['purchase.params.setting'].search([('name','=','purchase.request')])
        except:
            raise exceptions.ValidationError('Call Your Procurement Admin To set up the Price')
        for price in price_standard:
            arrMid.append(price.value_params)
        price = arrMid[1]
        return float(price)
    
    def get_user_sign(self):
        partner_id = False
        po_pr = self.env['purchase.request'].search([('id','=',self.request_id.id)])
        po_preq = self.env['purchase.requisition'].search([('origin','=',po_pr.complete_name)])
        office_level_code_procurement = None
        
        if(po_preq):
            employee = self.env['hr.employee'].search([('user_id','=',po_preq.user_id.id)])
            office_level_code_procurement = employee.office_level_id.code
            
        if office_level_code_procurement == 'KOKB':
            for mids in po_pr.message_ids:
                for mids_tracking in mids.tracking_value_ids:
                    if mids_tracking.field == 'state' and mids_tracking.old_value_char == 'RO Head Approval':
                        partner_id = mids.author_id
        elif office_level_code_procurement == 'KPST':
            if self.amount_total < self._get_price_mid():
                for mids in po_pr.message_ids:
                    for mids_tracking in mids.tracking_value_ids:
                        if mids_tracking.field == 'state' and mids_tracking.new_value_char == 'Director Financial Approval':
                            partner_id = mids.author_id
            else :
                for mids in po_pr.message_ids:
                    for mids_tracking in mids.tracking_value_ids:
                        if mids_tracking.field == 'state' and mids_tracking.old_value_char == 'Director Financial Approval':
                            partner_id = mids.author_id
        
        return partner_id
        
class InheritPurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    qty_request = fields.Float('Quantity Actual')
    validation_check_backorder = fields.Boolean('Confirm backorder',related='order_id.validation_check_backorder',store=True)
    spesification = fields.Text('Spesification')
    term_of_goods = fields.Selection([('indent','Indent'),('ready','Ready Stock')],'Term Of Goods')
    days = fields.Float('Days Of Indent')
