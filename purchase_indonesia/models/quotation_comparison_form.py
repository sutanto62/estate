from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from datetime import datetime, date,time
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re
from lxml import etree
from openerp.tools.translate import _
from openerp.tools import (drop_view_if_exists)
import babel.numbers
import decimal
import locale


class InheritPurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    comparison_id = fields.Many2one('quotation.comparison.form','QCF')

    def button_confirm(self, cr, uid, ids, context=None):
        res = super(InheritPurchaseOrder, self).button_confirm(cr, uid, ids, context=context)
        proc_obj = self.pool.get('procurement.order')
        stock_move_obj = self.pool.get('stock.move')
        for po in self.browse(cr, uid, ids, context=context):
            if po.requisition_id and (po.requisition_id.exclusive == 'exclusive'):
                for order in po.requisition_id.purchase_ids:
                    if order.id != po.id:
                        proc_ids = proc_obj.search(cr, uid, [('purchase_id', '=', order.id)])
                        if proc_ids and po.state == 'confirmed':
                            proc_obj.write(cr, uid, proc_ids, {'purchase_id': po.id})
                        order.button_cancel()
                    po.requisition_id.tender_done(context=context)
            for element in po.order_line:
                if element.product_id == po.requisition_id.procurement_id.product_id:
                    stock_move_obj.write(cr, uid, element.move_ids.ids, {
                        'procurement_id': po.requisition_id.procurement_id.id,
                        'move_dest_id': po.requisition_id.procurement_id.move_dest_id.id,
                        }, context=context)
                if not element.quantity_tendered:
                    if element.validation_check_backorder == True:
                        element.write({'quantity_tendered': element.qty_request})
                    else:
                        element.write({'quantity_tendered': element.product_qty})
        return res

class InheritPurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    comparison_id = fields.Many2one('quotation.comparison.form','QCF')
    trigger_state = fields.Boolean('Trigger State')
    trigger_draft = fields.Boolean('Trigger Draft')
    trigger_filter_cancel = fields.Boolean('Trigger Cancel',default=False,compute='_filter_cancel')
    price_subtotal_temp = fields.Float(string='Subtotal',compute='_amount_line_temp',digits_compute= dp.get_precision('Account'))
    price_subtotal_label = fields.Char(string='Subtotal',compute='_amount_line_label')

    @api.multi
    @api.depends('price_subtotal_temp','price_subtotal')
    def _amount_line_label(self):
        for item in self:
            if item.trigger_draft == True and item.quantity_tendered > 0:

                item.price_subtotal_label = item.price_subtotal_temp

            elif item.trigger_draft == False and item.quantity_tendered > 0:

                item.price_subtotal_label = item.price_subtotal

            else:
                item.price_subtotal_label = item.price_subtotal

    @api.multi
    @api.depends('quantity_tendered')
    def _amount_line_temp(self):
        for item in self:

            if item.quantity_tendered > 0 and item.trigger_draft == True and item.trigger_state == True:

                item.price_subtotal_temp = item.quantity_tendered * item.price_unit


    def button_confirm(self, cr, uid, ids, context=None):

        for element in self.browse(cr, uid, ids, context=context):
            if element.validation_check_backorder == False and element.qty_request == element.product_qty:

                self.write(cr, uid, element.id, {'trigger_state':True,'quantity_tendered': element.product_qty}, context=context)
            elif element.validation_check_backorder == False and not element.qty_request:

                self.write(cr, uid, element.id, {'trigger_state':True,'quantity_tendered': element.product_qty}, context=context)
            elif element.validation_check_backorder == False and element.qty_request :

                self.write(cr, uid, element.id, {'trigger_state':True,'quantity_tendered': element.qty_request}, context=context)
            else:

                self.write(cr, uid, element.id, {'trigger_state':True,'quantity_tendered': element.qty_request}, context=context)
        return True

    @api.multi
    def button_cancel(self):
        self.write({'trigger_state':False})
        res = super(InheritPurchaseOrderLine,self).button_cancel()
        return res

    @api.multi
    @api.depends('order_id')
    def _filter_cancel(self):
        for item in self:
            if item.order_id.state == 'cancel':
                item.trigger_filter_cancel = True



class QuotationComparisonForm(models.Model):

    def return_action_to_open(self, cr, uid, ids, context=None):
        """ This opens the xml view specified in xml_id for the current Purchase Tender """
        if context is None:
            context = {}
        if context.get('xml_id'):
            res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid ,'purchase', context['xml_id'], context=context)
            res['context'] = context
            res['context'].update({'default_comparison_id': ids[0]})
            res['domain'] = [('comparison_id','=',ids[0])]
            return res
        return False

    @api.multi
    def purchase_request_dpt_head(self):
        return self.env.ref('purchase_request.group_purchase_request_dept_head', False).id

    @api.multi
    def purchase_request_division_head(self):
        return self.env.ref('purchase_request.group_purchase_request_div_head', False).id

    @api.multi
    def purchase_request_budget(self):
        return self.env.ref('purchase_request.group_purchase_request_budget', False).id

    @api.multi
    def purchase_request_technical1(self):
        return self.env.ref('purchase_request.group_purchase_request_technical1', False).id

    @api.multi
    def purchase_request_technical2(self):
        return self.env.ref('purchase_request.group_purchase_request_technical2', False).id

    @api.multi
    def purchase_request_technical3(self):
        return self.env.ref('purchase_request.group_purchase_request_technical3', False).id

    @api.multi
    def purchase_request_technical4(self):
        return self.env.ref('purchase_request.group_purchase_request_technical4', False).id

    @api.multi
    def purchase_request_technical5(self):
        return self.env.ref('purchase_request.group_purchase_request_technical5', False).id

    @api.multi
    def purchase_request_technical6(self):
        return self.env.ref('purchase_indonesia.group_purchase_request_technical6', False).id

    @api.multi
    def purchase_request_director(self):
        return self.env.ref('purchase_indonesia.group_purchase_request_director', False).id

    @api.multi
    def purchase_request_president_director(self):
        return self.env.ref('purchase_indonesia.group_purchase_request_president_director', False).id

    @api.multi
    def purchase_ro_head(self):
        return self.env.ref('purchase_indonesia.group_purchase_request_head_of_ro', False).id

    @api.multi
    def purchase_procurement_staff(self):
        return self.env.ref('purchase_request.group_purchase_request_procstaff', False).id

    @api.multi
    def purchase_request_manager(self):
        return self.env.ref('purchase_request.group_purchase_request_manager', False).id

    @api.multi
    def purchase_request_finance(self):
        return self.env.ref('purchase_indonesia.group_purchase_request_finance_procurement', False).id

    #Method Get user
    @api.multi
    def _get_user(self):
        #find User
        user= self.env['res.users'].browse(self.env.uid)

        return user

    @api.multi
    def _get_employee(self):
        #find User Employee

        employee = self.env['hr.employee'].search([('user_id','=',self._get_user().id)])

        return employee

    @api.multi
    def _get_employee_request(self):
        #find User Employee

        employee = self.env['hr.employee'].search([('user_id','=',self.pic_id.id)])

        return employee

    @api.multi
    def _get_user_ro_manager(self):
        #get List of Ro Manager from user.groups
        arrRO = []

        list_ro_manager = self.env['res.groups'].search([('id','=',self.purchase_ro_head())]).users

        for ro_manager_id in list_ro_manager:
                arrRO.append(ro_manager_id.id)
        try:
            ro_manager = self.env['res.users'].search([('id','in',arrRO)]).id
        except:
            raise exceptions.ValidationError('User get Role President Director Not Found in User Access')

        return ro_manager

    @api.multi
    def _get_president_director(self):
        #get List of president director from user.groups
        arrPresidentDirector = []

        #search User President director from user list
        list_president= self.env['res.groups'].search([('id','=',self.purchase_request_president_director())]).users

        for president_id in list_president:
            arrPresidentDirector.append(president_id.id)
        try:
            president = self.env['res.users'].search([('id','=',arrPresidentDirector[0])]).id
        except:
            raise exceptions.ValidationError('User get Role President Director Not Found in User Access')
        return president

    @api.multi
    def _get_director(self):
        #get List of director from user.groups
        arrDirector = []

        #search User Director from user list
        list_director= self.env['res.groups'].search([('id','=',self.purchase_request_director())]).users
        for director_id in list_director:
            arrDirector.append(director_id.id)
        try:
            director = self.env['res.users'].search([('id','=',arrDirector[0])]).id
        except:
            raise exceptions.ValidationError('User get Role Director Purchase Not Found in User Access')
        return director

    @api.multi
    def _get_division_finance(self):
        #get List of Finance from user.groups
        arrDivhead = []

        #search User Finance from user list
        listdivision= self.env['res.groups'].search([('id','=',self.purchase_request_division_head())]).users

        for divhead in listdivision:
            arrDivhead.append(divhead.id)
        try:
            division = self.env['res.users'].search([('id','=',arrDivhead[0])]).id
        except:
            raise exceptions.ValidationError('User get Role Division Head Not Found in User Access')

        return division

    @api.multi
    def _get_procurement_finance(self):
        #get List of Finance from user.groups
        arrFinancehead = []
        arrEmployee = []

        #search User Finance from user list
        listprocurement= self.env['res.groups'].search([('id','=',self.purchase_request_finance())]).users

        for financeproc in listprocurement:
            arrFinancehead.append(financeproc.id)
        try:
            parent_employee = self._get_employee_request().parent_id.user_id.id
            fin_procur = self.env['res.users'].search([('id','in',arrFinancehead),('id','=',parent_employee)]).id
        except:
            raise exceptions.ValidationError('User get Role Finance Procurement Not Found in User Access')

        return fin_procur

    @api.multi
    def _get_employee_location(self):
        for item in self:
            hr = item.env['hr.employee']
            hr_location_code = hr.search([('user_id','=',item.pic_id.id)]).office_level_id.code

            return hr_location_code
    
    @api.model
    def _get_purchase_procurement_staff_group_id(self):
        return [('groups_id', '=', self.purchase_procurement_staff())]

    _name = 'quotation.comparison.form'
    _description = 'Form Quotation Comparison'
    _order = 'complete_name desc'
    _inherit=['mail.thread']

    name = fields.Char('name')
    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    date_pp = fields.Date('Date')
    type_location = fields.Char('Location')
    pic_id = fields.Many2one('res.users','Created By',domain=_get_purchase_procurement_staff_group_id)
    assign_to = fields.Many2one('res.users','Approver by')
    location = fields.Char('Location')
    origin = fields.Char('Source Purchase Request')
    partner_id = fields.Many2one('res.partner')
    company_id = fields.Many2one('res.company','Company')
    requisition_id = fields.Many2one('purchase.requisition','Purchase Requisition')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Send QCF'),
        ('confirm2','Send QCF RO'),
        ('approve','Approval Finance'),
        ('approve1', 'Approval GM Finance'),
        ('approve2','Approval Director'),
        ('approve3','Approval President Director'),
        ('approve4','Approval Head of the Representative Office'),
        ('done', 'Done'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled')], string="State",store=True,track_visibility='onchange')
    remarks = fields.Text('Remarks')
    validation_missing_product = fields.Boolean('Missing Product')
    validation_check_backorder = fields.Boolean('Confirm backorder')
    reject_reason = fields.Text('Reject Reason')
    line_remarks = fields.Integer(compute='_compute_line_remarks')
    # line_remarks_backorder = fields.Integer(compute='_compute_line_remarks_backorder')
    tracking_approval_ids = fields.One2many('tracking.approval','owner_id','Tracking Approval List')
    purchase_line_ids = fields.One2many('purchase.order.line','comparison_id','Order Line')
    partner_ids = fields.Many2many('res.partner',string='Vendors')
    backorder_purchase_line_ids = fields.One2many('purchase.order.line','comparison_id','Order Line',domain=[('validation_check_backorder','=',True)])
    quotation_comparison_line_ids = fields.One2many('quotation.comparison.form.line','qcf_id','Comparison Line')
    v_quotation_comparison_line_ids = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
    is_assign_to_user = fields.Boolean('Is Assign to User', compute='_compute_is_assign_to_user')
    pic_id_string = fields.Char('Created By', compute="_compute_pic_id_string")
#     v_quotation_comparison_line_ids2 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
#     v_quotation_comparison_line_ids3 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
#     v_quotation_comparison_line_ids4 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
#     v_quotation_comparison_line_ids5 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
#     v_quotation_comparison_line_ids6 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
#     v_quotation_comparison_line_ids7 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
#     v_quotation_comparison_line_ids8 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
#     v_quotation_comparison_line_ids9 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
#     v_quotation_comparison_line_ids10 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
    #Back Order
    # v_backorder_quotation_comparison_line_ids = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line',domain=[('backorder','=',True)])
    # v_backorder_quotation_comparison_line_ids2 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line',domain=[('backorder','=',True)])
    # v_backorder_quotation_comparison_line_ids3 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line',domain=[('backorder','=',True)])
    # v_backorder_quotation_comparison_line_ids4 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line',domain=[('backorder','=',True)])
    # v_backorder_quotation_comparison_line_ids5 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line',domain=[('backorder','=',True)])
    # v_backorder_quotation_comparison_line_ids6 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line',domain=[('backorder','=',True)])
    # v_backorder_quotation_comparison_line_ids7 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line',domain=[('backorder','=',True)])
    # v_backorder_quotation_comparison_line_ids8 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line',domain=[('backorder','=',True)])
    # v_backorder_quotation_comparison_line_ids9 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line',domain=[('backorder','=',True)])
    # v_backorder_quotation_comparison_line_ids10 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line',domain=[('backorder','=',True)])


    _defaults = {
        'state' : 'draft'
    }
    
    @api.multi
    def _compute_pic_id_string(self):
        for item in self:
            item.pic_id_string = item.pic_id.name
    
    @api.multi
    def _compute_is_assign_to_user(self):
        for item in self:
            item.is_assign_to_user = True if item.assign_to.id == self._get_user().id and item.state in ('approve','approve1','approve2','approve3','approve4') else False
    
    @api.multi
    def generated_po(self):
        for item in self:
            arrProductLine = []
            arrPurchase = []
            arrPurchaseProduct = []
            tender_line = item.env['purchase.requisition.line']
            purchase = item.env['purchase.order']
            purchase_line = item.env['purchase.order.line']

            product_tender_line = tender_line.search([('requisition_id','=',item.requisition_id.id)])
            for product in product_tender_line:
                arrProductLine.append(product.product_id.id)

            purchase_id = purchase.search([('requisition_id','=',item.requisition_id.id),('state','=','purchase'),('validation_check_backorder','=',False)])
            for purchase in purchase_id:
                arrPurchase.append(purchase.id)
            purchase_line_id = purchase_line.search([('order_id','in',arrPurchase)])
            for product_purchase in purchase_line_id:
                arrPurchaseProduct.append(product_purchase.product_id.id)

            set_product = set(arrProductLine)- set(arrPurchaseProduct)

            po_lines = item.env['purchase.requisition'].search([('id','=',item.requisition_id.id)])
            line_tender_missing = tender_line.search([('requisition_id','=',item.requisition_id.id),('product_id','in',list(set_product)),('check_missing_product','=',True)])

            if item.validation_missing_product == True:
                po_lines.generate_po()
                line_tender_missing.write({'check_missing_product' : False})
            else:
                po_lines.generate_po()

    @api.multi
    def _get_purchase_request(self):
        #get Purchase.request model
        purchase_request = self.env['purchase.request'].search([('complete_name','like',self.origin)])
        return purchase_request
    
    @api.multi
    def _get_max_price(self):
        for item in self:
            purchase_order = item.env['purchase.order']
            purchase_ids = purchase_order.search([('validation_check_backorder','=',True),('requisition_id','=',item.requisition_id.id)])
            # purchase_request_backorder = item.env['purchase.requisition'].search([('validation_check_backorder','=',True),('id','=',item.requisition_id.id)]).purchase_ids
            purchase_request_normalorder = item.env['purchase.requisition'].search([('validation_check_backorder','=',False),('id','=',item.requisition_id.id)]).purchase_ids
            arrBackorder = []

            if item.validation_check_backorder:
                for purchase in purchase_ids:
                    arrBackorder.append(purchase.amount_total)
                # price = max(purchase.amount_total for purchase in purchase_request_backorder)
                price = max(arrBackorder)
                return price
            else:
                price = max(purchase.amount_total for purchase in purchase_request_normalorder)
                return price

    @api.multi
    def _get_price_low(self):
        #get Minimal price from purchase params for Quotation comparison Form
        price_standard = self.env['purchase.params.setting'].search([('name','=',self._name)])
        price = min(float(price.value_params) for price in price_standard)
        return float(price)

    @api.multi
    def _get_price_mid(self):
        #get middle price from purchase params for Quotation comparison Form
        arrMid = []
        price_standard = self.env['purchase.params.setting'].search([('name','=',self._name)])
        for price in price_standard:
            arrMid.append(price.value_params)
        price = arrMid[1]
        return float(price)
    
    @api.multi
    def _get_price_high(self):
        #get Maximal price from purchase params for Quotation comparison Form
        price_standard = self.env['purchase.params.setting'].search([('name','=',self._name)])
        price = max(float(price.value_params) for price in price_standard)
        return float(price)

    @api.one
    @api.depends('name','date_pp','company_id','type_location')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d'

        if self.name and self.date_pp and self.company_id.code and self.type_location:
            date = self.date_pp
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
                                 + self.company_id.code+'-'\
                                 +'QCF'+'/'\
                                 +str(self.type_location)+'/'+str(month)+'/'+str(year)
        else:
            self.complete_name = self.name

        return True

    @api.multi
    @api.depends('line_remarks')
    def _compute_line_remarks(self):
        for item in self:
            item.env.cr.execute('select count(partner_id) from(select partner_id from quotation_comparison_form_line where qcf_id = %d group by partner_id)a' %(item.id))
            line = item.env.cr.fetchone()[0]
            item.line_remarks = line

    # @api.multi
    # @api.depends('line_remarks_backorder')
    # def _compute_line_remarks_backorder(self):
    #     for item in self:
    #         item.env.cr.execute('select count(partner_id) from(select partner_id from quotation_comparison_form_line where qcf_id = %d and (pol_po_backorder is not null or pol_po_backorder = True) group by partner_id)a' %(item.id))
    #         back_order_line = item.env.cr.fetchone()[0]
    #         item.line_remarks_backorder = back_order_line


    @api.multi
    def print_qcf(self):
        for item in self:
            arrPartner = []
            purchase_tender = item.env['purchase.requisition'].search([('id','=',item.requisition_id.id)])
            partner = item.env['purchase.order'].search([('requisition_id','=',purchase_tender.id)])
            for record in partner:
                arrPartner.append(record.partner_id.ids)
            partner_list = list(arrPartner)
            wizard_form = item.env.ref('purchase_indonesia.wizard_partner_comparison', False)
            view_id = item.env['wizard.partner.comparison']
            vals = {
                        'name'   : 'this is for set name',
                        'qcf_id' : item.id,
                        'partner_ids' : [(6, 0, partner_list)]
                    }
            new = view_id.create(vals)
            if not item.partner_ids:
                return {
                            'name'      : _('Print Your Quotation Comparison'),
                            'type'      : 'ir.actions.act_window',
                            'res_model' : 'wizard.partner.comparison',
                            'res_id'    : new.id,
                            'view_id'   : wizard_form.id,
                            'view_type' : 'form',
                            'view_mode' : 'form',
                            'target'    : 'new'
                        }
            else:
                return {
                        'name'      : _('Print Your Quotation Comparison'),
                        'type'      : 'ir.actions.act_window',
                        'res_model' : 'wizard.partner.comparison',
                        'res_id'    : new.id,
                        'view_id'   : wizard_form.id,
                        'view_type' : 'form',
                        'view_mode' : 'form',
                        'target'    : 'new'
                    }

    # @api.multi
    # def _create_wizard(self):
    #     for item in self:
    #         wizard_form = item.env.ref('purchase_indonesia.wizard_partner_comparison', False)
    #         view_id = item.env['wizard.partner.comparison']
    #         vals = {
    #                     'name'   : 'this is for set name',
    #                     'partner_ids' : [(6, 0, item.partner_ids.ids)]
    #                 }
    #         new = view_id.create(vals)


    @api.multi
    def action_send(self):
        for item in self:
            if item._get_user().id != item.pic_id.id:
                raise exceptions.ValidationError('You not PIC for This Quotation Comparison Form')
            else:
                arrPoid = []
                tender_line =item.env['purchase.requisition.line']
                tender_line_id = tender_line.search([('requisition_id','=',item.requisition_id.id)])
                purchase = item.env['purchase.order']
                purchase_ids = purchase.search([('comparison_id','=',item.id)])
                
#                 #check that we have at least confirm one line
#                 confirm = False
#                 for po_line in item.requisition_id.po_line_ids:
#                     if po_line.quantity_tendered > 0:
#                         confirm = True
#                         break
#                 if not confirm:
#                     raise exceptions.ValidationError('You have no line selected for buying.')
                
                #check that we have at least confirm one line
                confirm = False
                for po_line in item.purchase_line_ids:
                    if po_line.quantity_tendered > 0:
                        confirm = True
                        break
                if not confirm and len(item.purchase_line_ids) > 0:
                    raise exceptions.ValidationError('You have no line selected for buying.')
                
                confirm = False
                for po_line in item.backorder_purchase_line_ids:
                    if po_line.quantity_tendered > 0:
                        confirm = True
                        break
                if not confirm and len(item.backorder_purchase_line_ids) > 0:
                    raise exceptions.ValidationError('You have no line selected for buying.')
                    
                if purchase_ids:
                    for record in purchase_ids:
                        arrPoid.append(record.id)
                        
                    for tender in tender_line_id:

                        order_line_ids = item.env['purchase.order.line'].search([('order_id','in',arrPoid),('product_id','=',tender.product_id.id)])

                        for order in order_line_ids:
                            if order.quantity_tendered > tender.product_qty:
                                error_msg = 'Quantity tendered \"%s\" cannot more than Product Quantity \"%s\" in Tender Line'%(order.product_id.name,tender.product_id.name)
                                raise exceptions.ValidationError(error_msg)
                            else:
                                if item._get_employee_location() == 'KPST':
                                    item.write({'state' : 'approve','assign_to':item._get_procurement_finance()})
                                elif item._get_employee_location() in ['KOKB','KPWK']:
                                    item.write({'state' : 'approve4','assign_to':item._get_user_ro_manager()})
                self.send_mail_template()

        return True

    @api.multi
    def button_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.assign_to = None
            rec.send_mail_template_redraft()
        return True
    
    @api.multi
    def action_approve(self):
        
        #check that we have at least confirm one line
        confirm = False
        for po_line in self.requisition_id.po_line_ids:
            if po_line.quantity_tendered > 0:
                confirm = True
                break
        if not confirm:
            raise exceptions.ValidationError('You have no line selected for buying.')
        else:
            #approval finance head procurement
            if self._get_purchase_request().code in ['KPST','KOKB','KPWK'] :
                self.write({'state': 'approve1', 'assign_to': self._get_division_finance()})
                self.send_mail_template()

    @api.multi
    def action_approve1(self):
        #approval Gm finance
        if (self._get_purchase_request().code in ['KPST','KOKB','KPWK']  and self._get_max_price() < self._get_price_mid()) or (self._get_purchase_request().code in ['KPST','KOKB','KPWK'] and self._get_max_price() < self._get_price_mid()):
            self.write({'state' : 'done'})
            self.generated_po()
        elif (self._get_purchase_request().code in ['KPST','KOKB','KPWK']  and self._get_max_price() >= self._get_price_mid()) or (self._get_purchase_request().code in ['KPST','KOKB','KPWK'] and self._get_max_price() >= self._get_price_mid()):
            self.write({'state' : 'approve2','assign_to':self._get_director()})
            self.send_mail_template()

    @api.multi
    def action_approve2(self):
        #approval Director
        if self._get_purchase_request().code in ['KPST','KOKB','KPWK']  and self._get_max_price() >= self._get_price_mid() and self._get_max_price() < self._get_price_high() or self._get_purchase_request().code in ['KOKB','KPWK'] and self._get_max_price() >= self._get_price_mid() and self._get_max_price() < self._get_price_high():
            self.write({'state' : 'done'})
            self.generated_po()
        elif self._get_purchase_request().code in ['KPST','KOKB','KPWK']  and self._get_max_price() >= self._get_price_high() or self._get_purchase_request().code in ['KOKB','KPWK'] and self._get_max_price() >= self._get_price_high():
            self.write({'state' : 'approve3','assign_to':self._get_president_director()})
            self.send_mail_template()

    @api.multi
    def action_approve3(self):
        #approval President Director
        self.write({'state': 'done'})
        self.generated_po()
        return True

    @api.multi
    def action_approve4(self):
        #approval Ro Head
        if self._get_purchase_request().code in ['KOKB','KPWK'] and self._get_max_price() < self._get_price_low():
            #action Done
            self.write({'state' : 'done'})
            self.generated_po()
        elif self._get_purchase_request().code in ['KOKB','KPWK'] and (self._get_max_price() > self._get_price_low()):
            #action to send Procurement Finance
            self.write({'state' : 'approve','assign_to':self._get_procurement_finance()})
            self.send_mail_template()

        # elif self._get_purchase_request().code in ['KOKB','KPWK'] and self._get_max_price() >= self._get_price_mid() or self._get_purchase_request().code in ['KOKB','KPWK'] and self._get_max_price() > self._get_price_low() :
        #     #action to send Division Head Finance
        #     self.write({'state' : 'approve1','assign_to':self._get_division_finance()})
        #     self.send_mail_template()
        return True

    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done'})
        return True

    @api.multi
    def action_reject(self,):
        self.write({'state': 'reject'})
        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def tracking_approval(self):
        user= self.env['res.users'].browse(self.env.uid)
        employee = self.env['hr.employee'].search([('user_id','=',user.id)]).name_related
        current_date=str(datetime.now().today())
        # datetimeval=datetime.strptime(current_date, "%Y-%m-%d %H:%M:%S")
        tracking_data = {
            'owner_id': self.id,
            'state' : self.state,
            'name_user' : employee,
            'datetime'  :current_date
        }
        self.env['tracking.approval'].create(tracking_data)

    @api.multi
    def open_product_line(self,ids,context=None):
        """ This opens product line view to view all lines from the different quotations, groupby default by product and partner to show comparaison
            between vendor price
            @return: the product line tree view
        """
        if context is None:
            context = {}
        res = self.env['ir.actions.act_window'].for_xml_id('purchase_requisition', 'purchase_line_tree', context=context)
        res['context'] = context
        po_lines = self.env['purchase.requisition'].search([('id','=',self.requisition_id.id)]).po_line_ids
        requistion_id = self.requisition_id.id
        res['context'] = {
            'search_default_groupby_product': True,
            'search_default_hide_cancelled': True,
            'tender_id' : requistion_id,
        }
        res['domain'] = [('id', 'in', [line.id for line in po_lines])]
        return res

    @api.multi
    def change_remarks(self):
        self._get_value_purchase_order_line()

    @api.multi
    def _get_value_purchase_order_line(self):
        remarks = ''
        v_remarks = ''
        goods_name = ''
        vendor_name = ''
        payment_term = ''
        goods_price = ''
        delivery_term = ''
        incoterm = ''

        for item in self:

            order_line = item.env['purchase.order.line'].search([('comparison_id','=',item.id),('trigger_state','=',True)])

            for record in order_line:


                goods_name = '' if not record.product_id.name else record.product_id.name
                vendor_name = '' if not record.partner_id.name else record.partner_id.name
                goods_price = '' if not str(record.price_unit) else str(record.price_unit)

                #convert Goods Price to Currency IDR indonesia
                company_locale_name = ''
                company_currency_name = item.env['res.company'].search([('id','=',item.company_id.id)]).currency_id.name

                company = item.env['res.company'].search([('id','=',item.company_id.id)])

                company_locale_name = 'id_ID' if not company.locale_code else company.locale_code

                price = babel.numbers.format_currency( decimal.Decimal(goods_price), company_currency_name,locale=company_locale_name)

                purchase = item.env['purchase.order'].search([('id','=',record.order_id.id)])
                for record in purchase:
                    delivery_term = '' if not record.delivery_term else record.delivery_term
                    incoterm = '' if not record.incoterm_id.name else record.incoterm_id.name
                    payment_term = '' if not record.payment_term_id.name else record.payment_term_id.name

                v_remarks =  '* Item dengan nama barang '+' '+ goods_name \
                             +' Vendor yang di pilih adalah '+' '+vendor_name \
                             +' karena Kondisi Barang '+delivery_term\
                             +' memberikan harga kompetitif dengan harga '+price\
                             +' dengan klausul pembayaran '+payment_term\
                             +' incoterm bertipe ' + incoterm\
                             +'\n'+'\n'
                remarks = remarks + v_remarks

            item.remarks = remarks

    @api.multi
    @api.constrains('purchase_line_ids')
    def _constraint_purchase_line_ids(self):

        for item in self:

            arrPoid = []
            tender_line =item.env['purchase.requisition.line']
            tender_line_id = tender_line.search([('requisition_id','=',item.requisition_id.id)])
            purchase = item.env['purchase.order']
            purchase_ids = purchase.search([('comparison_id','=',item.id)])
            if purchase_ids:
                for record in purchase_ids:
                    arrPoid.append(record.id)

                for tender in tender_line_id:

                    order_line_ids = item.env['purchase.order.line'].search([('order_id','in',arrPoid),('product_id','=',tender.product_id.id)])

                    for order in order_line_ids:
                        if order.quantity_tendered > tender.product_qty:
                            error_msg = 'Quantity tendered \"%s\" cannot more than Product Quantity \"%s\" in Tender Line'%(order.product_id.name,tender.product_id.name)
                            raise exceptions.ValidationError(error_msg)

    #Email Template Code Starts Here

    @api.one
    def send_mail_template(self):

            # Find the e-mail template
            template = self.env.ref('purchase_indonesia.email_template_purchase_quotation_comparison')
            # You can also find the e-mail template like this:
            # template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
            # Send out the e-mail template to the user
            self.env['mail.template'].browse(template.id).send_mail(self.id,force_send=True)
            
    @api.one
    def send_mail_template_redraft(self):

            # Find the e-mail template
            template = self.env.ref('purchase_indonesia.email_template_purchase_quotation_comparison_draft')
            # You can also find the e-mail template like this:
            # template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
            # Send out the e-mail template to the user
            self.env['mail.template'].browse(template.id).send_mail(self.id,force_send=True)

    @api.multi
    def database(self):
        for item in self:
            #search DB name

            db = item.env.cr.dbname

            return db

    @api.multi
    def web_url(self):
        for item in self:
            # Search Web URL

            web = item.env['ir.config_parameter'].sudo().get_param('web.base.url')

            return web

    @api.multi
    def email_model(self):
        for item in self:
            #search Model

            model = item._name

            return model


class ViewPurchaseRequisition(models.Model):
    _name = 'view.purchase.requisition'
    _description = 'View Purchase Requisition'
    _auto = False
    _order = 'requisition_id'

    id = fields.Integer()
    qty_request = fields.Float('Quantity Request')
    requisition_id = fields.Many2one('purchase.requisition')
    product_id = fields.Many2one('product.product','Product')

    def init(self, cr):
        cr.execute("""create or replace view view_purchase_requisition as
                        select row_number() over() id,
                                product_id,product_qty as qty_request,requisition_id
                                      from purchase_requisition pr
                        inner join purchase_requisition_line prl on prl.requisition_id = pr.id""")

class ViewComparisonLine(models.Model):

    _name = 'view.comparison.line'
    _description = 'Quotation Comparison Line'
    _auto = False
    _order = 'req_id'

    id = fields.Integer()
    rownum = fields.Integer()
    cheapest = fields.Integer()
    req_id = fields.Many2one('purchase.requisition')
    qcf_id = fields.Many2one('quotation.comparison.form')
    company_id = fields.Many2one('res.company','Company')
    product_id = fields.Many2one('product.product','Product')
    product_uom = fields.Many2one('product.uom','Unit Of Measurement')
    partner_id = fields.Many2one('res.partner','Vendor')
    price_unit = fields.Float('Price Unit')
    price_subtotal = fields.Float('Price Subtotal')
    amount_untaxed = fields.Float('Amount Untaxed')
    price_tax = fields.Float('Price Tax')
    amount_total = fields.Float('Amount Total')
    payment_term_id = fields.Many2one('account.payment.term','Payment Term')
    date_planned = fields.Datetime('Planned Date')
    incoterm_id = fields.Many2one('stock.incoterms','Incoterms')
    delivery_term = fields.Char('Delivery Term')
    po_des_all_name = fields.Text('Description')
    pol_po_backorder = fields.Boolean('Back Order')
    trigger_state = fields.Char('Trigger State')

    def init(self, cr):
        drop_view_if_exists(cr, 'view_comparison_line')
        cr.execute("""create or replace view view_comparison_line
            as
            SELECT
                (po_pol_all.pol_id)::bigint AS id,
                po_pol_all.pol_po_backorder,
                po_pol_all.qcf_id,
                po_pol_all.com_id AS company_id,
                po_pol_all.req_id,
                po_pol_all.product_id,
                row_number() OVER (PARTITION BY po_pol_all.req_id, po_pol_all.product_id ORDER BY po_pol_all.product_id) AS rownum,
                po_pol_all.product_uom,
                po_pol_all.part_id AS partner_id,
                po_pol_all.price_unit,
                po_pol_all.price_subtotal,
                po_pol_all.amount_untaxed,
                po_pol_all.price_tax,
                po_pol_all.amount_total,
                po_pol_all.payment_term_id,
                po_pol_all.date_planned,
                po_pol_all.incoterm_id,
                po_pol_all.delivery_term,
                po_pol_min.cheapest,
                po_pol_all.po_des_all_name,
                po_pol_all.trigger_state
               FROM (
                           ( 
                       SELECT 
                           qcf_po.pol_des_name AS po_des_all_name,
                        qcf.id AS qcf_id,
                        qcf.requisition_id AS req_id,
                        qcf_po.po_backorder AS pol_po_backorder,
                        qcf_po.pol_id,
                        qcf_po.com_id,
                        qcf_po.part_id,
                        qcf_po.amount_untaxed,
                        qcf_po.incoterm_id,
                        qcf_po.payment_term_id,
                        qcf_po.amount_total,
                        qcf_po.delivery_term,
                        qcf_po.product_uom,
                        qcf_po.price_unit,
                        qcf_po.price_subtotal,
                        qcf_po.price_tax,
                        qcf_po.product_id,
                        qcf_po.date_planned,
                        qcf_po.trigger_state
                       FROM (quotation_comparison_form qcf
                         JOIN ( 
                             SELECT 
                                 pol.id AS pol_id,
                                po.company_id AS com_id,
                                po.partner_id AS part_id,
                                po.validation_check_backorder AS po_backorder,
                                pol.pol_name AS pol_des_name,
                                po.id,
                                po.amount_untaxed,
                                po.incoterm_id,
                                po.payment_term_id,
                                po.amount_total,
                                po.requisition_id,
                                po.delivery_term,
                                pol.product_uom,
                                pol.price_unit,
                                pol.price_subtotal,
                                pol.price_tax,
                                pol.product_id,
                                pol.date_planned,
                                pol.trigger_state
                               FROM (purchase_order po
                                 JOIN ( SELECT 
                                         purchase_order_line.name AS pol_name,
                                        purchase_order_line.id,
                                        purchase_order_line.product_uom,
                                        purchase_order_line.price_unit,
                                        purchase_order_line.price_subtotal,
                                        purchase_order_line.partner_id,
                                        purchase_order_line.price_tax,
                                        purchase_order_line.company_id,
                                        purchase_order_line.order_id,
                                        purchase_order_line.product_id,
                                        purchase_order_line.date_planned,
                                        purchase_order_line.trigger_state,
                                        purchase_order_line.validation_check_backorder
                                       FROM purchase_order_line
                                     ) pol 
                                     ON (
                                             (
                                                 (po.id = pol.order_id) AND (po.requisition_id IS NOT NULL)
                                             )
                                         )
                                 )
                               ) qcf_po
                           ON (
                                   (qcf.requisition_id = qcf_po.requisition_id)
                               )
                           )
                       ) po_pol_all
                 JOIN ( 
                         SELECT 
                             po_pol.requisition_id,
                            po_pol.product_id,
                            min(po_pol.price_subtotal) AS cheapest
                           FROM ( 
                               SELECT 
                                po.requisition_id,
                                pol.price_subtotal,
                                pol.product_id
                               FROM (purchase_order po
                                 JOIN ( 
                                         SELECT 
                                            purchase_order_line.price_subtotal,
                                            purchase_order_line.order_id,
                                            purchase_order_line.product_id
                                           FROM 
                                               purchase_order_line
                                       ) pol 
                                           ON (
                                                   (
                                                       (po.id = pol.order_id) AND (po.requisition_id IS NOT NULL)
                                                   )
                                               )
                                       )
                                )po_pol
                      GROUP BY 
                          po_pol.requisition_id, po_pol.product_id
                    ) po_pol_min 
                    ON 
                    (
                        (
                            (po_pol_all.req_id = po_pol_min.requisition_id) 
                            AND 
                            (po_pol_all.product_id = po_pol_min.product_id)
                        )
                    )
            );""")

class QuotationComparisonFormLine(models.Model):

    _name = 'quotation.comparison.form.line'
    _description = 'Quotation Comparison Line'
    _auto = False
    _order = 'req_id'

    id = fields.Integer()
    rownum = fields.Integer()
    cheapest = fields.Integer()
    req_id = fields.Many2one('purchase.requisition')
    qcf_id = fields.Many2one('quotation.comparison.form')
    company_id = fields.Many2one('res.company','Company')
    product_id = fields.Many2one('product.product','Product')
    qty_request = fields.Float('Quantity Request')
    product_uom = fields.Many2one('product.uom','Unit Of Measurement')
    partner_id = fields.Many2one('res.partner','Vendor')
    price_unit = fields.Float('Price Unit')
    price_subtotal = fields.Float('Price Subtotal')
    amount_untaxed = fields.Float('Amount Untaxed')
    price_tax = fields.Float('Price Tax')
    amount_total = fields.Float('Amount Total')
    payment_term_id = fields.Many2one('account.payment.term','Payment Term')
    date_planned = fields.Datetime('Planned Date')
    incoterm_id = fields.Many2one('stock.incoterms','Incoterms')
    delivery_term = fields.Char('Delivery Term')
    po_des_all_name = fields.Text('Description')
    pol_po_backorder = fields.Boolean('Back Order')
    trigger_state = fields.Char('Trigger State')

    def init(self, cr):
        drop_view_if_exists(cr, 'quotation_comparison_form_line')
        cr.execute("""create or replace view quotation_comparison_form_line
                as
                SELECT vcl.id,
                    vcl.pol_po_backorder,
                    vcl.qcf_id,
                    vcl.company_id,
                    vcl.req_id,
                    vpr.product_id,
                    vcl.rownum,
                    vcl.product_uom,
                    vcl.partner_id,
                    vcl.price_unit,
                    vcl.price_subtotal,
                    vcl.amount_untaxed,
                    vcl.price_tax,
                    vcl.amount_total,
                    vpr.qty_request,
                    vcl.payment_term_id,
                    vcl.date_planned,
                    vcl.incoterm_id,
                    vcl.delivery_term,
                    vcl.cheapest,
                    vcl.po_des_all_name,
                    vcl.trigger_state
                   FROM (view_comparison_line vcl
                     JOIN view_purchase_requisition vpr ON (((vcl.req_id = vpr.requisition_id) AND (vpr.product_id = vcl.product_id))));
                        """)


#Query Back Order
# class BackOrderQuotationComparisonFormLine(models.Model):
#
#     _name = 'backorder.quotation.comparison.form.line'
#     _description = 'Back Order Quotation Comparison Line'
#     _auto = False
#     _order = 'req_id'
#
#     id = fields.Integer()
#     rownum = fields.Integer()
#     cheapest = fields.Integer()
#     req_id = fields.Many2one('purchase.requisition')
#     qcf_id = fields.Many2one('quotation.comparison.form')
#     company_id = fields.Many2one('res.company','Company')
#     product_id = fields.Many2one('product.product','Product')
#     qty_request = fields.Float('Quantity Request')
#     product_uom = fields.Many2one('product.uom','Unit Of Measurement')
#     partner_id = fields.Many2one('res.partner','Vendor')
#     price_unit = fields.Float('Price Unit')
#     price_subtotal = fields.Float('Price Subtotal')
#     amount_untaxed = fields.Float('Amount Untaxed')
#     price_tax = fields.Float('Price Tax')
#     amount_total = fields.Float('Amount Total')
#     payment_term_id = fields.Many2one('account.payment.term','Payment Term')
#     date_planned = fields.Datetime('Planned Date')
#     incoterm_id = fields.Many2one('stock.incoterms','Incoterms')
#     delivery_term = fields.Char('Delivery Term')
#     po_des_all_name = fields.Text('Description')
#
#
#     def init(self, cr):
#         cr.execute("""create or replace view backorder_quotation_comparison_form_line as
#                     select row_number() over() id,qcf_id,
#                             com_id company_id,req_id,
#                             po_pol_all.product_id,
#                             row_number() over (partition by req_id,po_pol_all.product_id order by po_pol_all.product_id asc) rownum,
#                             qty_request,
#                             product_uom,
#                             part_id partner_id,
#                             price_unit,
#                             price_subtotal,
#                             amount_untaxed,
#                             price_tax,
#                             amount_total,
#                             payment_term_id,date_planned,incoterm_id,delivery_term,
#                             po_pol_min.cheapest,po_des_all_name from
#                     (
#                     select
#                     	pol_des_name po_des_all_name,
#                     	qcf.id qcf_id,
#                     	qcf.requisition_id req_id,*
#                     from quotation_comparison_form qcf
#                     inner join (
#                         select
#                         	row_number() over() id,
#                         	po.company_id com_id,
#                         	po.partner_id part_id,
#                         	pol.pol_name pol_des_name,*
#                             from purchase_order po inner join (
#                                 select name pol_name,* from purchase_order_line
#                                     )pol on po.id = pol.order_id and po.requisition_id is not null and po.validation_check_backorder = True
#                                     )qcf_po on qcf.requisition_id = qcf_po.requisition_id
#                                     where qcf.validation_check_backorder = True
#                             )po_pol_all
#                         inner join
#                         (
#                             select requisition_id, product_id, min(price_subtotal) cheapest
#                             from (
#                                 select * from purchase_order po inner join (
#                                     select * from purchase_order_line
#                                 )pol on po.id = pol.order_id and po.requisition_id is not null
#                             )po_pol group by po_pol.requisition_id, product_id
#                         ) po_pol_min
#                         on po_pol_all.req_id = po_pol_min.requisition_id and po_pol_all.product_id = po_pol_min.product_id
#                         """)


class ViewQuotationComparison(models.Model):

    _name = 'v.quotation.comparison.form.line'
    _description = 'Quotation Comparison Line'
    _auto = False
    _order = 'isheader asc'


    id = fields.Integer()
    isheader = fields.Integer()
    grand_total_label = fields.Char(compute='_is_grand_total_label')
    qcf_id = fields.Many2one('quotation.comparison.form')
    req_id = fields.Many2one('purchase.requisition')
    product_id = fields.Many2one('product.product','Product')
    last_price = fields.Float('Last Price')
    last_price_char = fields.Char('Last Price')
    write_date = fields.Datetime('Last Date PO')
    qty_request = fields.Char('Quantity Request')
    product_uom = fields.Many2one('product.uom','Unit Of Measurement')
    vendor1 = fields.Char('Vendor')
    vendor2 = fields.Char('Vendor')
    vendor3 = fields.Char('Vendor')
    vendor4 = fields.Char('Vendor')
    vendor5 = fields.Char('Vendor')
    vendor6 = fields.Char('Vendor')
    vendor7 = fields.Char('Vendor')
    vendor8 = fields.Char('Vendor')
    vendor9 = fields.Char('Vendor')
    vendor10 = fields.Char('Vendor')
    po_des_all_name = fields.Text('Description')
    hide = fields.Boolean()
    validation_check_backorder=fields.Boolean('Back Order')

    def init(self, cr):
        cr.execute("""CREATE OR REPLACE FUNCTION monetary(input_value float)
                    RETURNS varchar
                     LANGUAGE plpgsql
                     STRICT
                    AS $function$
                    DECLARE
                    BEGIN
                        return case when (input_value = 0)
                        then  '0'
                        else to_char(input_value,'FM999G999G999G999G999G999G999G999D00')
                        end;
                    END
        		    $function$""")

        drop_view_if_exists(cr, 'v_quotation_comparison_form_line')


        cr.execute("""create or replace view v_quotation_comparison_form_line as
             SELECT last_price.validation_check_backorder,
                qcf_line.id,
                qcf_line.req_id,
                qcf_line.product_id,
                qcf_line.hide,
                qcf_line.grand_total_label,
                qcf_line.qty_request,
                qcf_line.product_uom,
                qcf_line.vendor1,
                qcf_line.vendor2,
                qcf_line.vendor3,
                qcf_line.vendor4,
                qcf_line.vendor5,
                qcf_line.vendor6,
                qcf_line.vendor7,
                qcf_line.vendor8,
                qcf_line.vendor9,
                qcf_line.vendor10,
                qcf_line.po_des_all_name,
                qcf_line.isheader,
                qcf_line.qcf_id,
                last_price.last_price,
                last_price.write_date,
                '' AS last_price_char
               FROM (( SELECT row_number() OVER () AS id,
                        vqcf.req_id,
                        vqcf.product_id,
                        vqcf.hide,
                        vqcf.grand_total_label,
                        vqcf.qty_request,
                        vqcf.product_uom,
                        vqcf.vendor1,
                        vqcf.vendor2,
                        vqcf.vendor3,
                        vqcf.vendor4,
                        vqcf.vendor5,
                        vqcf.vendor6,
                        vqcf.vendor7,
                        vqcf.vendor8,
                        vqcf.vendor9,
                        vqcf.vendor10,
                        vqcf.po_des_all_name,
                        vqcf.isheader,
                        qcf.id AS qcf_id
                       FROM 
                       (
                               ( 
                               SELECT 
                                header.req_id,
                                header.product_id,
                                header.hide,
                                header.grand_total_label,
                                header.qty_request,
                                header.product_uom,
                                header.vendor1,
                                header.vendor2,
                                header.vendor3,
                                header.vendor4,
                                header.vendor5,
                                header.vendor6,
                                header.vendor7,
                                header.vendor8,
                                header.vendor9,
                                header.vendor10,
                                header.po_des_all_name,
                                header.isheader
                               FROM ( 
                                       SELECT 
                                           r.req_id,
                                        0 AS product_id,
                                        (0)::boolean AS hide,
                                        ''::character varying AS grand_total_label,
                                        ''::character varying AS qty_request,
                                        0 AS product_uom,
                                        ''::character varying AS po_des_all_name,
                                           2 AS isheader,
                                        max((
                                        CASE
                                         WHEN (r.rownum = 1) THEN r.name
                                         ELSE NULL::character varying
                                        END)::text) AS vendor1,
                                          max((
                                        CASE
                                         WHEN (r.rownum = 2) THEN r.name
                                         ELSE NULL::character varying
                                        END)::text) AS vendor2,
                                          max((
                                        CASE
                                         WHEN (r.rownum = 3) THEN r.name
                                         ELSE NULL::character varying
                                        END)::text) AS vendor3,
                                        max((
                                        CASE
                                         WHEN (r.rownum = 4) THEN r.name
                                         ELSE NULL::character varying
                                        END)::text) AS vendor4,
                                        max((
                                        CASE
                                         WHEN (r.rownum = 5) THEN r.name
                                         ELSE NULL::character varying
                                        END)::text) AS vendor5,
                                        max((
                                        CASE
                                         WHEN (r.rownum = 6) THEN r.name
                                         ELSE NULL::character varying
                                        END)::text) AS vendor6,
                                        max((
                                        CASE
                                         WHEN (r.rownum = 7) THEN r.name
                                         ELSE NULL::character varying
                                        END)::text) AS vendor7,
                                        max((
                                        CASE
                                         WHEN (r.rownum = 8) THEN r.name
                                         ELSE NULL::character varying
                                        END)::text) AS vendor8,
                                        max((
                                        CASE
                                         WHEN (r.rownum = 9) THEN r.name
                                         ELSE NULL::character varying
                                        END)::text) AS vendor9,
                                        max((
                                        CASE
                                         WHEN (r.rownum = 10) THEN r.name
                                         ELSE NULL::character varying
                                        END)::text) AS vendor10
                                   FROM ( 
                                           SELECT 
                                            DENSE_RANK() OVER (PARTITION BY qcfl.req_id ORDER BY qcfl.partner_id DESC NULLS LAST) as rownum,   
                                            partner.name,
                                            qcfl.req_id,
                                            qcfl.product_id,
                                            qcfl.qty_request,
                                            qcfl.product_uom,
                                            qcfl.price_unit,
                                            qcfl.price_subtotal,
                                            qcfl.price_tax,
                                            qcfl.payment_term_id,
                                            qcfl.incoterm_id,
                                            qcfl.delivery_term,
                                            qcfl.po_des_all_name
                                           FROM
                                                  quotation_comparison_form_line qcfl
                                                  JOIN ( 
                                                     SELECT 
                                                         res_partner.id,
                                                          res_partner.name
                                                     FROM 
                                                         res_partner
                                                     ) partner ON qcfl.partner_id = partner.id
                                         ) r
                                           GROUP BY r.req_id
                                 ) header
                            UNION ALL
                                 SELECT 
                                    content.req_id,
                                    content.product_id,
                                    content.hide,
                                    content.grand_total_label,
                                    content.qty_request,
                                    content.product_uom,
                                    content.vendor1,
                                    content.vendor2,
                                    content.vendor3,
                                    content.vendor4,
                                    content.vendor5,
                                    content.vendor6,
                                    content.vendor7,
                                    content.vendor8,
                                    content.vendor9,
                                    content.vendor10,
                                    content.po_des_all_name,
                                    content.isheader
                                FROM(
                                    SELECT 
                                        content1.req_id,
                                        content1.product_id,
                                        content1.hide,
                                        content1.grand_total_label,
                                        content1.qty_request,
                                        content1.product_uom,
                                        content1.vendor1,
                                        content1.vendor2,
                                        content1.vendor3,
                                        content1.vendor4,
                                        content1.vendor5,
                                        content1.vendor6,
                                        content1.vendor7,
                                        content1.vendor8,
                                        content1.vendor9,
                                        content1.vendor10,
                                        content1.po_des_all_name,
                                        content1.isheader
                                   FROM ( SELECT r.req_id,
                                            r.product_id,
                                            (0)::boolean AS hide,
                                            ''::character varying AS grand_total_label,
                                            (r.qty_request)::character varying AS qty_request,
                                            r.product_uom,
                                            max((
                                                CASE
                                                    WHEN (r.rownum = 1) THEN r.trigger_state || monetary((r.price_unit)::double precision)
                                                    ELSE NULL::character varying
                                                END)::text) AS vendor1,
                                            max((
                                                CASE
                                                    WHEN (r.rownum = 2) THEN r.trigger_state || monetary((r.price_unit)::double precision)
                                                    ELSE NULL::character varying
                                                END)::text) AS vendor2,
                                            max((
                                                CASE
                                                    WHEN (r.rownum = 3) THEN r.trigger_state || monetary((r.price_unit)::double precision)
                                                    ELSE NULL::character varying
                                                END)::text) AS vendor3,
                                            max((
                                                CASE
                                                    WHEN (r.rownum = 4) THEN r.trigger_state || monetary((r.price_unit)::double precision)
                                                    ELSE NULL::character varying
                                                END)::text) AS vendor4,
                                            max((
                                                CASE
                                                    WHEN (r.rownum = 5) THEN r.trigger_state || monetary((r.price_unit)::double precision)
                                                    ELSE NULL::character varying
                                                END)::text) AS vendor5,
                                            max((
                                                CASE
                                                    WHEN (r.rownum = 6) THEN r.trigger_state || monetary((r.price_unit)::double precision)
                                                    ELSE NULL::character varying
                                                END)::text) AS vendor6,
                                            max((
                                                CASE
                                                    WHEN (r.rownum = 7) THEN r.trigger_state || monetary((r.price_unit)::double precision)
                                                    ELSE NULL::character varying
                                                END)::text) AS vendor7,
                                            max((
                                                CASE
                                                    WHEN (r.rownum = 8) THEN r.trigger_state || monetary((r.price_unit)::double precision)
                                                    ELSE NULL::character varying
                                                END)::text) AS vendor8,
                                            max((
                                                CASE
                                                    WHEN (r.rownum = 9) THEN r.trigger_state || monetary((r.price_unit)::double precision)
                                                    ELSE NULL::character varying
                                                END)::text) AS vendor9,
                                            max((
                                                CASE
                                                    WHEN (r.rownum = 10) THEN r.trigger_state || monetary((r.price_unit)::double precision)
                                                    ELSE NULL::character varying
                                                END)::text) AS vendor10,
                                            (max(r.po_des_all_name))::character varying AS po_des_all_name,
                                            3 AS isheader
                                           FROM ( 
                                                   SELECT 
                                                       DENSE_RANK() OVER (PARTITION BY qcfl.req_id ORDER BY qcfl.partner_id DESC NULLS LAST) as rownum,
                                                    partner.name,
                                                    qcfl.req_id,
                                                    qcfl.product_id,
                                                    qcfl.qty_request,
                                                    qcfl.product_uom,
                                                    qcfl.price_unit,
                                                    qcfl.price_subtotal,
                                                    qcfl.price_tax,
                                                    qcfl.payment_term_id,
                                                    qcfl.incoterm_id,
                                                    qcfl.delivery_term,
                                                    qcfl.po_des_all_name,
                                                    case when qcfl.trigger_state = true then '* ' else '' end trigger_state
                                                   FROM
                                                               quotation_comparison_form_line qcfl
                                                            JOIN ( 
                                                                SELECT 
                                                                    res_partner.id,
                                                                    res_partner.name
                                                                   FROM 
                                                                       res_partner
                                                           ) partner 
                                                           ON qcfl.partner_id = partner.id
                                                       ) r
                                                  GROUP BY 
                                                      r.product_id, r.req_id, r.qty_request, r.product_uom
                                                    order by 
                                                        r.product_id asc
                                          ) content1 inner join product_product pp on content1.product_id = pp.id
                                            order by
                                                pp.default_code,pp.name_template
                                    )content
                            UNION ALL
                                 SELECT 
                                    footer1.req_id,
                                    footer1.product_id,
                                    footer1.hide,
                                    footer1.grand_total_label,
                                    footer1.qty_request,
                                    footer1.product_uom,
                                    footer1.vendor1,
                                    footer1.vendor2,
                                    footer1.vendor3,
                                    footer1.vendor4,
                                    footer1.vendor5,
                                    footer1.vendor6,
                                    footer1.vendor7,
                                    footer1.vendor8,
                                    footer1.vendor9,
                                    footer1.vendor10,
                                    footer1.po_des_all_name,
                                    footer1.isheader
                               FROM ( 
                                           SELECT 
                                               h.req_id,
                                            0 AS product_id,
                                            (0)::boolean AS hide,
                                            ''::character varying AS grand_total_label,
                                            ''::character varying AS qty_request,
                                            0 AS product_uom,
                                            monetary((sum(h.vendor1))::double precision) AS vendor1,
                                            monetary((sum(h.vendor2))::double precision) AS vendor2,
                                            monetary((sum(h.vendor3))::double precision) AS vendor3,
                                            monetary((sum(h.vendor4))::double precision) AS vendor4,
                                            monetary((sum(h.vendor5))::double precision) AS vendor5,
                                            monetary((sum(h.vendor6))::double precision) AS vendor6,
                                            monetary((sum(h.vendor7))::double precision) AS vendor7,
                                            monetary((sum(h.vendor8))::double precision) AS vendor8,
                                            monetary((sum(h.vendor9))::double precision) AS vendor9,
                                            monetary((sum(h.vendor10))::double precision) AS vendor10,
                                            ''::character varying AS po_des_all_name,
                                            4 AS isheader
                                       FROM ( 
                                               SELECT 
                                                   r.req_id,
                                                r.product_id,
                                                r.qty_request,
                                                r.product_uom,
                                                max(
                                                CASE
                                                 WHEN (r.rownum = 1) THEN r.price_subtotal
                                                 ELSE NULL::numeric
                                                END) AS vendor1,
                                                max(
                                                CASE
                                                 WHEN (r.rownum = 2) THEN r.price_subtotal
                                                 ELSE NULL::numeric
                                                END) AS vendor2,
                                                max(
                                                CASE
                                                 WHEN (r.rownum = 3) THEN r.price_subtotal
                                                 ELSE NULL::numeric
                                                END) AS vendor3,
                                                max(
                                                CASE
                                                 WHEN (r.rownum = 4) THEN r.price_subtotal
                                                 ELSE NULL::numeric
                                                END) AS vendor4,
                                                max(
                                                CASE
                                                 WHEN (r.rownum = 5) THEN r.price_subtotal
                                                 ELSE NULL::numeric
                                                END) AS vendor5,
                                                max(
                                                CASE
                                                 WHEN (r.rownum = 6) THEN r.price_subtotal
                                                 ELSE NULL::numeric
                                                END) AS vendor6,
                                                max(
                                                CASE
                                                 WHEN (r.rownum = 7) THEN r.price_subtotal
                                                 ELSE NULL::numeric
                                                END) AS vendor7,
                                                max(
                                                CASE
                                                 WHEN (r.rownum = 8) THEN r.price_subtotal
                                                 ELSE NULL::numeric
                                                END) AS vendor8,
                                                max(
                                                CASE
                                                 WHEN (r.rownum = 9) THEN r.price_subtotal
                                                 ELSE NULL::numeric
                                                END) AS vendor9,
                                                max(
                                                CASE
                                                 WHEN (r.rownum = 10) THEN r.price_subtotal
                                                 ELSE NULL::numeric
                                                END) AS vendor10
                                               FROM ( 
                                                       SELECT 
                                                        DENSE_RANK() OVER (PARTITION BY qcfl.req_id ORDER BY qcfl.partner_id DESC NULLS LAST) as rownum,
                                                        partner.name,
                                                        qcfl.req_id,
                                                        qcfl.product_id,
                                                        qcfl.qty_request,
                                                        qcfl.product_uom,
                                                        qcfl.price_unit,
                                                        qcfl.price_subtotal,
                                                        qcfl.price_tax,
                                                        qcfl.payment_term_id,
                                                        qcfl.incoterm_id,
                                                        qcfl.delivery_term,
                                                        qcfl.po_des_all_name
                                                   FROM
                                                         quotation_comparison_form_line qcfl
                                                         JOIN ( 
                                                             SELECT 
                                                                 res_partner.id,
                                                                  res_partner.name
                                                             FROM 
                                                                 res_partner
                                                         ) partner ON qcfl.partner_id = partner.id
                                                     ) r
                                              GROUP BY r.product_id, r.req_id, r.qty_request, r.product_uom
                                              ) h
                                      GROUP BY h.req_id) footer1
                            UNION ALL
                                     SELECT 
                                               footer2.req_id,
                                            footer2.product_id,
                                            footer2.hide,
                                            footer2.grand_total_label,
                                            footer2.qty_request,
                                            footer2.product_uom,
                                            footer2.vendor1,
                                            footer2.vendor2,
                                            footer2.vendor3,
                                            footer2.vendor4,
                                            footer2.vendor5,
                                            footer2.vendor6,
                                            footer2.vendor7,
                                            footer2.vendor8,
                                            footer2.vendor9,
                                            footer2.vendor10,
                                            footer2.po_des_all_name,
                                            footer2.isheader
                                       FROM ( 
                                           SELECT 
                                               h.req_id,
                                            0 AS product_id,
                                            (0)::boolean AS hide,
                                            ''::character varying AS grand_total_label,
                                            ''::character varying AS qty_request,
                                            0 AS product_uom,
                                            monetary((sum(h.vendor1))::double precision) AS vendor1,
                                            monetary((sum(h.vendor2))::double precision) AS vendor2,
                                            monetary((sum(h.vendor3))::double precision) AS vendor3,
                                            monetary((sum(h.vendor4))::double precision) AS vendor4,
                                            monetary((sum(h.vendor5))::double precision) AS vendor5,
                                            monetary((sum(h.vendor6))::double precision) AS vendor6,
                                            monetary((sum(h.vendor7))::double precision) AS vendor7,
                                            monetary((sum(h.vendor8))::double precision) AS vendor8,
                                            monetary((sum(h.vendor9))::double precision) AS vendor9,
                                            monetary((sum(h.vendor10))::double precision) AS vendor10,
                                            ''::character varying AS po_des_all_name,
                                            5 AS isheader
                                       FROM ( 
                                                   SELECT 
                                                       r.req_id,
                                                    r.product_id,
                                                    r.qty_request,
                                                    r.product_uom,
                                                    max(
                                                    CASE
                                                     WHEN (r.rownum = 1) THEN r.price_tax
                                                     ELSE NULL::numeric
                                                    END) AS vendor1,
                                                    max(
                                                    CASE
                                                     WHEN (r.rownum = 2) THEN r.price_tax
                                                     ELSE NULL::numeric
                                                    END) AS vendor2,
                                                    max(
                                                    CASE
                                                     WHEN (r.rownum = 3) THEN r.price_tax
                                                     ELSE NULL::numeric
                                                    END) AS vendor3,
                                                    max(
                                                    CASE
                                                     WHEN (r.rownum = 4) THEN r.price_tax
                                                     ELSE NULL::numeric
                                                    END) AS vendor4,
                                                    max(
                                                    CASE
                                                     WHEN (r.rownum = 5) THEN r.price_tax
                                                     ELSE NULL::numeric
                                                    END) AS vendor5,
                                                    max(
                                                    CASE
                                                     WHEN (r.rownum = 6) THEN r.price_tax
                                                     ELSE NULL::numeric
                                                    END) AS vendor6,
                                                    max(
                                                    CASE
                                                     WHEN (r.rownum = 7) THEN r.price_tax
                                                     ELSE NULL::numeric
                                                    END) AS vendor7,
                                                    max(
                                                    CASE
                                                     WHEN (r.rownum = 8) THEN r.price_tax
                                                     ELSE NULL::numeric
                                                    END) AS vendor8,
                                                    max(
                                                    CASE
                                                     WHEN (r.rownum = 9) THEN r.price_tax
                                                     ELSE NULL::numeric
                                                    END) AS vendor9,
                                                    max(
                                                    CASE
                                                     WHEN (r.rownum = 10) THEN r.price_tax
                                                     ELSE NULL::numeric
                                                    END) AS vendor10
                                               FROM ( 
                                                       SELECT 
                                                        DENSE_RANK() OVER (PARTITION BY qcfl.req_id ORDER BY qcfl.partner_id DESC NULLS LAST) as rownum,
                                                        partner.name,
                                                        qcfl.req_id,
                                                        qcfl.product_id,
                                                        qcfl.qty_request,
                                                        qcfl.product_uom,
                                                        qcfl.price_unit,
                                                        qcfl.price_subtotal,
                                                        qcfl.price_tax,
                                                        qcfl.payment_term_id,
                                                        qcfl.incoterm_id,
                                                        qcfl.delivery_term,
                                                        qcfl.po_des_all_name
                                                   FROM 
                                                          quotation_comparison_form_line qcfl
                                                           JOIN ( 
                                                             SELECT 
                                                                 res_partner.id,
                                                                  res_partner.name
                                                             FROM 
                                                                 res_partner
                                                         ) partner ON 
                                                         qcfl.partner_id = partner.id
                                                    ) r
                                                      GROUP BY r.product_id, r.req_id, r.qty_request, r.product_uom
                                                      ) h
                                                  GROUP BY h.req_id) footer2
                            UNION ALL
                                             SELECT 
                                                       footer.req_id,
                                                    footer.product_id,
                                                    footer.hide,
                                                    footer.grand_total_label,
                                                    footer.qty_request,
                                                    footer.product_uom,
                                                    footer.vendor1,
                                                    footer.vendor2,
                                                    footer.vendor3,
                                                    footer.vendor4,
                                                    footer.vendor5,
                                                    footer.vendor6,
                                                    footer.vendor7,
                                                    footer.vendor8,
                                                    footer.vendor9,
                                                    footer.vendor10,
                                                    footer.po_des_all_name,
                                                    footer.isheader
                                               FROM ( 
                                                       SELECT 
                                                           h.req_id,
                                                        0 AS product_id,
                                                        (0)::boolean AS hide,
                                                        ''::character varying AS grand_total_label,
                                                        ''::character varying AS qty_request,
                                                        0 AS product_uom,
                                                        monetary((sum(h.vendor1))::double precision) AS vendor1,
                                                        monetary((sum(h.vendor2))::double precision) AS vendor2,
                                                        monetary((sum(h.vendor3))::double precision) AS vendor3,
                                                        monetary((sum(h.vendor4))::double precision) AS vendor4,
                                                        monetary((sum(h.vendor5))::double precision) AS vendor5,
                                                        monetary((sum(h.vendor6))::double precision) AS vendor6,
                                                        monetary((sum(h.vendor7))::double precision) AS vendor7,
                                                        monetary((sum(h.vendor8))::double precision) AS vendor8,
                                                        monetary((sum(h.vendor9))::double precision) AS vendor9,
                                                        monetary((sum(h.vendor10))::double precision) AS vendor10,
                                                        ''::character varying AS po_des_all_name,
                                                        6 AS isheader
                                                      FROM ( 
                                                           SELECT 
                                                               r.req_id,
                                                               r.product_id,
                                                              r.qty_request,
                                                              r.product_uom,
                                                            max(
                                                            CASE
                                                             WHEN (r.rownum = 1) THEN r.amount_total
                                                             ELSE NULL::numeric
                                                            END) AS vendor1,
                                                            max(
                                                            CASE
                                                             WHEN (r.rownum = 2) THEN r.amount_total
                                                             ELSE NULL::numeric
                                                            END) AS vendor2,
                                                            max(
                                                            CASE
                                                             WHEN (r.rownum = 3) THEN r.amount_total
                                                             ELSE NULL::numeric
                                                            END) AS vendor3,
                                                            max(
                                                            CASE
                                                             WHEN (r.rownum = 4) THEN r.amount_total
                                                             ELSE NULL::numeric
                                                            END) AS vendor4,
                                                            max(
                                                            CASE
                                                             WHEN (r.rownum = 5) THEN r.amount_total
                                                             ELSE NULL::numeric
                                                            END) AS vendor5,
                                                            max(
                                                            CASE
                                                             WHEN (r.rownum = 6) THEN r.amount_total
                                                             ELSE NULL::numeric
                                                            END) AS vendor6,
                                                            max(
                                                            CASE
                                                             WHEN (r.rownum = 7) THEN r.amount_total
                                                             ELSE NULL::numeric
                                                            END) AS vendor7,
                                                            max(
                                                            CASE
                                                             WHEN (r.rownum = 8) THEN r.amount_total
                                                             ELSE NULL::numeric
                                                            END) AS vendor8,
                                                            max(
                                                            CASE
                                                             WHEN (r.rownum = 9) THEN r.amount_total
                                                             ELSE NULL::numeric
                                                            END) AS vendor9,
                                                            max(
                                                            CASE
                                                             WHEN (r.rownum = 10) THEN r.amount_total
                                                             ELSE NULL::numeric
                                                            END) AS vendor10
                                                           FROM ( 
                                                               SELECT 
                                                                    DENSE_RANK() OVER (PARTITION BY qcfl.req_id ORDER BY qcfl.partner_id DESC NULLS LAST) as rownum,
                                                                    partner.name,
                                                                    qcfl.req_id,
                                                                    qcfl.product_id,
                                                                    qcfl.qty_request,
                                                                    qcfl.product_uom,
                                                                    qcfl.price_unit,
                                                                    (qcfl.price_subtotal + qcfl.price_tax) AS amount_total,
                                                                    qcfl.price_tax,
                                                                    qcfl.payment_term_id,
                                                                    qcfl.incoterm_id,
                                                                    qcfl.delivery_term,
                                                                    qcfl.po_des_all_name
                                                               FROM
                                                                      quotation_comparison_form_line qcfl
                                                                     JOIN ( 
                                                                         SELECT 
                                                                             res_partner.id,
                                                                              res_partner.name
                                                                         FROM 
                                                                             res_partner) 
                                                                     partner ON qcfl.partner_id = partner.id
                                                             ) r
                                              GROUP BY r.product_id, r.req_id, r.qty_request, r.product_uom
                                              ) h
                                      GROUP BY h.req_id) footer
                            UNION ALL
                                    SELECT 
                                              paymentterm.req_id,
                                            paymentterm.product_id,
                                            paymentterm.hide,
                                            paymentterm.grand_total_label,
                                            paymentterm.qty_request,
                                            paymentterm.product_uom,
                                            paymentterm.vendor1,
                                            paymentterm.vendor2,
                                            paymentterm.vendor3,
                                            paymentterm.vendor4,
                                            paymentterm.vendor5,
                                            paymentterm.vendor6,
                                            paymentterm.vendor7,
                                            paymentterm.vendor8,
                                            paymentterm.vendor9,
                                            paymentterm.vendor10,
                                            paymentterm.po_des_all_name,
                                            paymentterm.isheader
                                           FROM ( 
                                               SELECT 
                                                   h.req_id,
                                                0 AS product_id,
                                                (0)::boolean AS hide,
                                                ''::character varying AS grand_total_label,
                                                ''::character varying AS qty_request,
                                                0 AS product_uom,
                                                h.vendor1 AS vendor1,
                                                h.vendor2 AS vendor2,
                                                h.vendor3 AS vendor3,
                                                h.vendor4 AS vendor4,
                                                h.vendor5 AS vendor5,
                                                h.vendor6 AS vendor6,
                                                h.vendor7 AS vendor7,
                                                h.vendor8 AS vendor8,
                                                h.vendor9 AS vendor9,
                                                h.vendor10 AS vendor10,
                                                ''::character varying AS po_des_all_name,
                                                7 AS isheader
                                               FROM ( 
                                                   SELECT 
                                                       r.req_id,
                                                    max((
                                                    CASE
                                                     WHEN (r.rownum = 1) THEN r.name_term
                                                     ELSE NULL::character varying
                                                    END)::text) AS vendor1,
                                                    max((
                                                    CASE
                                                     WHEN (r.rownum = 2) THEN r.name_term
                                                     ELSE NULL::character varying
                                                    END)::text) AS vendor2,
                                                    max((
                                                    CASE
                                                     WHEN (r.rownum = 3) THEN r.name_term
                                                     ELSE NULL::character varying
                                                    END)::text) AS vendor3,
                                                    max((
                                                    CASE
                                                     WHEN (r.rownum = 4) THEN r.name_term
                                                     ELSE NULL::character varying
                                                    END)::text) AS vendor4,
                                                    max((
                                                    CASE
                                                     WHEN (r.rownum = 5) THEN r.name_term
                                                     ELSE NULL::character varying
                                                    END)::text) AS vendor5,
                                                    max((
                                                    CASE
                                                     WHEN (r.rownum = 6) THEN r.name_term
                                                     ELSE NULL::character varying
                                                    END)::text) AS vendor6,
                                                    max((
                                                    CASE
                                                     WHEN (r.rownum = 7) THEN r.name_term
                                                     ELSE NULL::character varying
                                                    END)::text) AS vendor7,
                                                    max((
                                                    CASE
                                                     WHEN (r.rownum = 8) THEN r.name_term
                                                     ELSE NULL::character varying
                                                    END)::text) AS vendor8,
                                                    max((
                                                    CASE
                                                     WHEN (r.rownum = 9) THEN r.name_term
                                                     ELSE NULL::character varying
                                                    END)::text) AS vendor9,
                                                    max((
                                                    CASE
                                                     WHEN (r.rownum = 10) THEN r.name_term
                                                     ELSE NULL::character varying
                                                    END)::text) AS vendor10
                                               FROM ( 
                                                       SELECT 
                                                        DENSE_RANK() OVER (PARTITION BY qcfl.req_id ORDER BY qcfl.partner_id DESC NULLS LAST) as rownum,
                                                        partner.name,
                                                        qcfl.req_id,
                                                        qcfl.product_id,
                                                        qcfl.qty_request,
                                                        qcfl.product_uom,
                                                        qcfl.price_unit,
                                                        qcfl.price_subtotal,
                                                        qcfl.price_tax,
                                                        payterm.name_term,
                                                        incoterm.name_inco,
                                                        qcfl.delivery_term,
                                                        qcfl.po_des_all_name
                                                   FROM 
                                                          quotation_comparison_form_line qcfl
                                                         JOIN ( 
                                                             SELECT 
                                                                 res_partner.id,
                                                                  res_partner.name
                                                             FROM 
                                                                 res_partner
                                                         ) partner 
                                                         ON qcfl.partner_id = partner.id
                                                   LEFT JOIN ( 
                                                       SELECT 
                                                           apt.id AS apt_id,
                                                          apt.name AS name_term
                                                      FROM 
                                                          account_payment_term apt
                                                      ) payterm 
                                                      ON qcfl.payment_term_id = payterm.apt_id
                                                   LEFT JOIN ( 
                                                       SELECT 
                                                           si.id AS si_id,
                                                          si.name AS name_inco
                                                      FROM 
                                                          stock_incoterms si
                                                   ) incoterm 
                                                   ON qcfl.incoterm_id = incoterm.si_id
                                              ) r
                                              GROUP BY r.req_id
                                          ) h
                                      ) paymentterm
                            UNION ALL
                                SELECT 
                                          deliverydate.req_id,
                                        deliverydate.product_id,
                                        deliverydate.hide,
                                        deliverydate.grand_total_label,
                                        deliverydate.qty_request,
                                        deliverydate.product_uom,
                                        deliverydate.vendor1,
                                        deliverydate.vendor2,
                                        deliverydate.vendor3,
                                        deliverydate.vendor4,
                                        deliverydate.vendor5,
                                        deliverydate.vendor6,
                                        deliverydate.vendor7,
                                        deliverydate.vendor8,
                                        deliverydate.vendor9,
                                        deliverydate.vendor10,
                                        deliverydate.po_des_all_name,
                                        deliverydate.isheader
                                       FROM ( 
                                           SELECT 
                                               h.req_id,
                                            0 AS product_id,
                                            (0)::boolean AS hide,
                                            ''::character varying AS grand_total_label,
                                            ''::character varying AS qty_request,
                                            0 AS product_uom,
                                            h.vendor1 AS vendor1,
                                            h.vendor2 AS vendor2,
                                            h.vendor3 AS vendor3,
                                            h.vendor4 AS vendor4,
                                            h.vendor5 AS vendor5,
                                            h.vendor6 AS vendor6,
                                            h.vendor7 AS vendor7,
                                            h.vendor8 AS vendor8,
                                            h.vendor9 AS vendor9,
                                            h.vendor10 AS vendor10,
                                            ''::character varying AS po_des_all_name,
                                            8 AS isheader
                                       FROM ( 
                                               SELECT 
                                                   r.req_id,
                                                max((
                                                CASE
                                                 WHEN (r.rownum = 1) THEN r.delivery_term
                                                 ELSE NULL::character varying
                                                END)::text) AS vendor1,
                                                max((
                                                CASE
                                                 WHEN (r.rownum = 2) THEN r.delivery_term
                                                 ELSE NULL::character varying
                                                END)::text) AS vendor2,
                                                max((
                                                CASE
                                                 WHEN (r.rownum = 3) THEN r.delivery_term
                                                 ELSE NULL::character varying
                                                END)::text) AS vendor3,
                                                max((
                                                CASE
                                                 WHEN (r.rownum = 4) THEN r.delivery_term
                                                 ELSE NULL::character varying
                                                END)::text) AS vendor4,
                                                max((
                                                CASE
                                                 WHEN (r.rownum = 5) THEN r.delivery_term
                                                 ELSE NULL::character varying
                                                END)::text) AS vendor5,
                                                max((
                                                CASE
                                                 WHEN (r.rownum = 6) THEN r.delivery_term
                                                 ELSE NULL::character varying
                                                END)::text) AS vendor6,
                                                max((
                                                CASE
                                                 WHEN (r.rownum = 7) THEN r.delivery_term
                                                 ELSE NULL::character varying
                                                END)::text) AS vendor7,
                                                max((
                                                CASE
                                                 WHEN (r.rownum = 8) THEN r.delivery_term
                                                 ELSE NULL::character varying
                                                END)::text) AS vendor8,
                                                max((
                                                CASE
                                                 WHEN (r.rownum = 9) THEN r.delivery_term
                                                 ELSE NULL::character varying
                                                END)::text) AS vendor9,
                                                max((
                                                CASE
                                                 WHEN (r.rownum = 10) THEN r.delivery_term
                                                 ELSE NULL::character varying
                                                END)::text) AS vendor10
                                               FROM ( 
                                                       SELECT 
                                                        qcfl.pol_po_backorder backorder,
                                                        DENSE_RANK() OVER (PARTITION BY qcfl.req_id ORDER BY qcfl.partner_id DESC NULLS LAST) as rownum,
                                                        partner.name,
                                                        qcfl.req_id,
                                                        qcfl.product_id,
                                                        qcfl.qty_request,
                                                        qcfl.product_uom,
                                                        qcfl.price_unit,
                                                        qcfl.price_subtotal,
                                                        qcfl.price_tax,
                                                        payterm.name_term,
                                                        incoterm.name_inco,
                                                        qcfl.delivery_term,
                                                        qcfl.po_des_all_name
                                                   FROM 
                                                          quotation_comparison_form_line qcfl
                                                         JOIN ( 
                                                             SELECT 
                                                                 res_partner.id,
                                                                  res_partner.name
                                                             FROM 
                                                                 res_partner
                                                         ) partner 
                                                     ON qcfl.partner_id = partner.id
                                                     LEFT JOIN ( 
                                                         SELECT 
                                                             apt.id AS apt_id,
                                                              apt.name AS name_term
                                                         FROM 
                                                             account_payment_term apt
                                                     ) payterm 
                                                     ON qcfl.payment_term_id = payterm.apt_id
                                                     LEFT JOIN ( 
                                                         SELECT 
                                                             si.id AS si_id,
                                                              si.name AS name_inco
                                                         FROM 
                                                             stock_incoterms si
                                                     ) incoterm 
                                                     ON qcfl.incoterm_id = incoterm.si_id
                                                     ) r
                                              GROUP BY r.req_id
                                              ) h
                                         ) deliverydate
                            UNION ALL
                                     SELECT 
                                               franco.req_id,
                                            franco.product_id,
                                            franco.hide,
                                            franco.grand_total_label,
                                            franco.qty_request,
                                            franco.product_uom,
                                            franco.vendor1,
                                            franco.vendor2,
                                            franco.vendor3,
                                            franco.vendor4,
                                            franco.vendor5,
                                            franco.vendor6,
                                            franco.vendor7,
                                            franco.vendor8,
                                            franco.vendor9,
                                            franco.vendor10,
                                            franco.po_des_all_name,
                                            franco.isheader
                                           FROM 
                                               ( 
                                                   SELECT 
                                                       h.req_id,
                                                    0 AS product_id,
                                                    (0)::boolean AS hide,
                                                    ''::character varying AS grand_total_label,
                                                    ''::character varying AS qty_request,
                                                    0 AS product_uom,
                                                    h.vendor1 AS vendor1,
                                                    h.vendor2 AS vendor2,
                                                    h.vendor3 AS vendor3,
                                                    h.vendor4 AS vendor4,
                                                    h.vendor5 AS vendor5,
                                                    h.vendor6 AS vendor6,
                                                    h.vendor7 AS vendor7,
                                                    h.vendor8 AS vendor8,
                                                    h.vendor9 AS vendor9,
                                                    h.vendor10 AS vendor10,
                                                    ''::character varying AS po_des_all_name,
                                                    9 AS isheader
                                                   FROM ( 
                                                       SELECT 
                                                           r.req_id,
                                                        max((
                                                        CASE
                                                         WHEN (r.rownum = 1) THEN r.name_inco
                                                         ELSE NULL::character varying
                                                        END)::text) AS vendor1,
                                                        max((
                                                        CASE
                                                         WHEN (r.rownum = 2) THEN r.name_inco
                                                         ELSE NULL::character varying
                                                        END)::text) AS vendor2,
                                                        max((
                                                        CASE
                                                         WHEN (r.rownum = 3) THEN r.name_inco
                                                         ELSE NULL::character varying
                                                        END)::text) AS vendor3,
                                                        max((
                                                        CASE
                                                         WHEN (r.rownum = 4) THEN r.name_inco
                                                         ELSE NULL::character varying
                                                        END)::text) AS vendor4,
                                                        max((
                                                        CASE
                                                         WHEN (r.rownum = 5) THEN r.name_inco
                                                         ELSE NULL::character varying
                                                        END)::text) AS vendor5,
                                                        max((
                                                        CASE
                                                         WHEN (r.rownum = 6) THEN r.name_inco
                                                         ELSE NULL::character varying
                                                        END)::text) AS vendor6,
                                                        max((
                                                        CASE
                                                         WHEN (r.rownum = 7) THEN r.name_inco
                                                         ELSE NULL::character varying
                                                        END)::text) AS vendor7,
                                                        max((
                                                        CASE
                                                         WHEN (r.rownum = 8) THEN r.name_inco
                                                         ELSE NULL::character varying
                                                        END)::text) AS vendor8,
                                                        max((
                                                        CASE
                                                         WHEN (r.rownum = 9) THEN r.name_inco
                                                         ELSE NULL::character varying
                                                        END)::text) AS vendor9,
                                                        max((
                                                        CASE
                                                         WHEN (r.rownum = 10) THEN r.name_inco
                                                         ELSE NULL::character varying
                                                        END)::text) AS vendor10
                                                   FROM ( 
                                                           SELECT 
                                                            DENSE_RANK() OVER (PARTITION BY qcfl.req_id ORDER BY qcfl.partner_id DESC NULLS LAST) as rownum,
                                                            partner.name,
                                                            qcfl.req_id,
                                                            qcfl.product_id,
                                                            qcfl.qty_request,
                                                            qcfl.product_uom,
                                                            qcfl.price_unit,
                                                            qcfl.price_subtotal,
                                                            qcfl.price_tax,
                                                            payterm.name_term,
                                                            incoterm.name_inco,
                                                            qcfl.delivery_term,
                                                            qcfl.po_des_all_name
                                                           FROM 
                                                             quotation_comparison_form_line qcfl
                                                              JOIN ( 
                                                                  SELECT 
                                                                      res_partner.id,
                                                                      res_partner.name
                                                                 FROM 
                                                                     res_partner
                                                             ) partner 
                                                             ON qcfl.partner_id = partner.id
                                                             LEFT JOIN ( 
                                                                 SELECT 
                                                                     apt.id AS apt_id,
                                                                      apt.name AS name_term
                                                                 FROM 
                                                                     account_payment_term apt) payterm 
                                                                     ON qcfl.payment_term_id = payterm.apt_id
                                                             LEFT JOIN ( 
                                                                SELECT 
                                                                    si.id AS si_id,
                                                                      si.name AS name_inco
                                                                 FROM 
                                                                     stock_incoterms si
                                                            ) incoterm 
                                                            ON qcfl.incoterm_id = incoterm.si_id
                                                        ) r
                                              GROUP BY r.req_id
                                              ) h
                                      ) franco
                                 ) vqcf
                         JOIN quotation_comparison_form qcf ON ((vqcf.req_id = qcf.requisition_id)))) qcf_line
                 LEFT JOIN ( SELECT b.rank_id,
                        b.product_id,
                        b.last_price,
                        b.write_date,
                        b.validation_check_backorder
                       FROM ( SELECT row_number() OVER (PARTITION BY a.po_id ORDER BY a.write_date DESC NULLS LAST) AS rank_id,
                                a.po_id,
                                a.validation_check_backorder,
                                a.order_id,
                                a.product_id,
                                a.last_price,
                                a.state,
                                a.write_date
                               FROM ( SELECT po.id AS po_id,
                                        po.validation_check_backorder,
                                        pol.order_id,
                                        pol.product_id,
                                        pol.price_unit AS last_price,
                                        po.state,
                                        po.write_date
                                       FROM (purchase_order po
                                         LEFT JOIN ( SELECT purchase_order_line.id,
                                                purchase_order_line.order_id,
                                                purchase_order_line.product_id,
                                                purchase_order_line.price_total,
                                                purchase_order_line.price_unit,
                                                purchase_order_line.product_qty
                                               FROM purchase_order_line) pol ON ((po.id = pol.order_id)))
                                      WHERE ((po.state)::text = 'done'::text)
                                      GROUP BY po.id, pol.order_id, pol.product_id, pol.price_total, pol.price_unit, pol.product_qty) a) b
                      WHERE (b.rank_id = 1)) last_price ON ((qcf_line.product_id = last_price.product_id)));
                      """)


    @api.multi
    @api.depends('qty_request')
    def _is_grand_total_label(self):
        for rec in self :
            if rec.isheader == 1:
                rec.po_des_all_name = ''
                rec.last_price = ''
                rec.write_date = ''
            elif rec.isheader == 2:
                rec.qty_request = 'xxx'
                rec.po_des_all_name = ''
                rec.write_date = ''
            elif rec.isheader == 3:
                rec.po_des_all_name = ''+rec.po_des_all_name
                rec.grand_total_label = ''
                rec.qty_request = str(rec.qty_request)
                rec.last_price_char = str(rec.last_price)
            elif rec.isheader == 4:
                rec.qty_request = 'Sub Total'
                rec.po_des_all_name = ''
                rec.write_date = ''
            elif rec.isheader == 5:
                rec.qty_request = 'Tax %'
                rec.po_des_all_name = ''
                rec.write_date = ''
            elif rec.isheader == 6:
                rec.qty_request = 'Grand Total'
                rec.po_des_all_name = ''
                rec.write_date = ''
            elif rec.isheader == 7:
                rec.qty_request = 'TOP'
                rec.po_des_all_name = ''
                rec.last_price = ''
                rec.write_date = ''
            elif rec.isheader == 8:
                rec.qty_request = 'Delivery'
                rec.po_des_all_name = ''
                rec.write_date = ''
            elif rec.isheader == 9:
                rec.qty_request = 'Incoterm/FRANCO'
                rec.po_des_all_name = ''
                rec.write_date = ''

# class ViewBackOrderQuotationComparison(models.Model):
#
#     _name = 'v.backorder.quotation.comparison.form.line'
#     _description = 'Back Order Quotation Comparison Line'
#     _auto = False
#     _order = 'isheader asc'
#
#     id = fields.Integer()
#     isheader = fields.Integer()
#     grand_total_label = fields.Char(compute='_is_grand_total_label')
#     qcf_id = fields.Many2one('quotation.comparison.form')
#     req_id = fields.Many2one('purchase.requisition')
#     product_id = fields.Many2one('product.product','Product')
#     last_price = fields.Float('Last Price')
#     last_price_char = fields.Char('Last Price')
#     write_date = fields.Datetime('Last Date PO')
#     qty_request = fields.Char('Quantity Request')
#     product_uom = fields.Many2one('product.uom','Unit Of Measurement')
#     vendor1 = fields.Char('Vendor')
#     vendor2 = fields.Char('Vendor')
#     vendor3 = fields.Char('Vendor')
#     vendor4 = fields.Char('Vendor')
#     vendor5 = fields.Char('Vendor')
#     vendor6 = fields.Char('Vendor')
#     vendor7 = fields.Char('Vendor')
#     vendor8 = fields.Char('Vendor')
#     vendor9 = fields.Char('Vendor')
#     vendor10 = fields.Char('Vendor')
#     po_des_all_name = fields.Text('Description')
#     hide = fields.Boolean()
#
#     def init(self, cr):
#         cr.execute("""CREATE OR REPLACE FUNCTION monetary(input_value float)
#                     RETURNS varchar
#                      LANGUAGE plpgsql
#                      STRICT
#                     AS $function$
#                     DECLARE
#                     BEGIN
#                         return case when (input_value = 0)
#                         then  '0'
#                         else to_char(input_value,'FM999G999G999G999G999G999G999G999D00')
#                         end;
#                     END
#         		    $function$""")
#
#         cr.execute("""create or replace view v_backorder_quotation_comparison_form_line as
#                         select qcf_line.*, last_price.last_price, last_price.write_date, '' last_price_char from (
#                         select row_number() over() id,vqcf.*,qcf.id qcf_id from (
#                                                             select * from (
#                                         select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,max(vendor1) vendor1,max(vendor2) vendor2,max(vendor3) vendor3,max(vendor4) vendor4,max(vendor5) vendor5,max(vendor6) vendor6,max(vendor7) vendor7,max(vendor8) vendor8,max(vendor9) vendor9,max(vendor10) vendor10,cast('' as varchar) po_des_all_name,2 isheader from (
#                                             SELECT r.req_id,r.product_id,qty_request,product_uom,
#                                                      MAX(CASE WHEN r.rownum = 1 THEN r.name ELSE NULL END) AS "vendor1",
#                                                      MAX(CASE WHEN r.rownum = 2 THEN r.name ELSE NULL END) AS "vendor2",
#                                                      MAX(CASE WHEN r.rownum = 3 THEN r.name ELSE NULL END) AS "vendor3",
#                                                      MAX(CASE WHEN r.rownum = 4 THEN r.name ELSE NULL END) AS "vendor4",
#                                                      MAX(CASE WHEN r.rownum = 5 THEN r.name ELSE NULL END) AS "vendor5",
#                                                      MAX(CASE WHEN r.rownum = 6 THEN r.name ELSE NULL END) AS "vendor6",
#                                                      MAX(CASE WHEN r.rownum = 7 THEN r.name ELSE NULL END) AS "vendor7",
#                                                      MAX(CASE WHEN r.rownum = 8 THEN r.name ELSE NULL END) AS "vendor8",
#                                                      MAX(CASE WHEN r.rownum = 9 THEN r.name ELSE NULL END) AS "vendor9",
#                                                      MAX(CASE WHEN r.rownum = 10 THEN r.name ELSE NULL END) AS "vendor10"
#                                                 FROM  (select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term,po_des_all_name from (
#                                                   select qcfl_rn.id rownum,company_id,po_des_all_name,
#                                                     qcfl_rn.req_id,qcfl_rn.partner_id,
#                                                     product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from backorder_quotation_comparison_form_line qcfl inner join (
#                                                                 select row_number() over(PARTITION BY req_id
#                                                                             ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
#                                                                             from  backorder_quotation_comparison_form_line
#                                                                             group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
#                                                 )con_qcfl_rn inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id) r
#                                             GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
#                                         )h group by req_id)header
#                                          union all
#                                          select * from (
#                                            SELECT r.req_id,r.product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast(qty_request as varchar) qty_request,product_uom,
#                                                  MAX(CASE WHEN r.rownum = 1 THEN CAST(monetary(r.price_unit) as varchar)  ELSE NULL END) AS "vendor1",
#                                                  MAX(CASE WHEN r.rownum = 2 THEN CAST(monetary(r.price_unit) as varchar)  ELSE NULL END) AS "vendor2",
#                                                  MAX(CASE WHEN r.rownum = 3 THEN CAST(monetary(r.price_unit) as varchar)  ELSE NULL END) AS "vendor3",
#                                                  MAX(CASE WHEN r.rownum = 4 THEN CAST(monetary(r.price_unit) as varchar)  ELSE NULL END) AS "vendor4",
#                                                  MAX(CASE WHEN r.rownum = 5 THEN CAST(monetary(r.price_unit) as varchar)  ELSE NULL END) AS "vendor5",
#                                                  MAX(CASE WHEN r.rownum = 6 THEN CAST(monetary(r.price_unit) as varchar)  ELSE NULL END) AS "vendor6",
#                                                  MAX(CASE WHEN r.rownum = 7 THEN CAST(monetary(r.price_unit) as varchar)  ELSE NULL END) AS "vendor7",
#                                                  MAX(CASE WHEN r.rownum = 8 THEN CAST(monetary(r.price_unit) as varchar)  ELSE NULL END) AS "vendor8",
#                                                  MAX(CASE WHEN r.rownum = 9 THEN CAST(monetary(r.price_unit) as varchar)  ELSE NULL END) AS "vendor9",
#                                                  MAX(CASE WHEN r.rownum = 10 THEN CAST(monetary(r.price_unit) as varchar)  ELSE NULL END) AS "vendor10",cast(max(po_des_all_name)as varchar) po_des_all_name,3 isheader
#                                             FROM  (select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term,po_des_all_name from (
#                                               select qcfl_rn.id rownum,company_id,po_des_all_name,
#                                                 qcfl_rn.req_id,qcfl_rn.partner_id,
#                                                 product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from backorder_quotation_comparison_form_line qcfl inner join (
#                                                             select row_number() over(PARTITION BY req_id
#                                                                         ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
#                                                                         from  backorder_quotation_comparison_form_line
#                                                                         group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
#                                             )con_qcfl_rn inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id) r
#                                         GROUP BY r.product_id,r.req_id,qty_request,product_uom,po_des_all_name  order by req_id asc )content
#                                         union all
#                                         select * from (
#                                         select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,
#                                         cast(monetary(sum(vendor1))  as varchar)  vendor1,cast(monetary(sum(vendor2)) as varchar) vendor2,
#                                         cast(monetary(sum(vendor3)) as varchar)  vendor3,cast(monetary(sum(vendor4)) as varchar) vendor4,
#                                         cast(monetary(sum(vendor5)) as varchar)  vendor5,cast(monetary(sum(vendor6)) as varchar) vendor6,
#                                         cast(monetary(sum(vendor7)) as varchar)  vendor7,cast(monetary(sum(vendor8)) as varchar) vendor8,
#                                         cast(monetary(sum(vendor9)) as varchar)  vendor9,cast(monetary(sum(vendor10)) as varchar) vendor10,cast('' as varchar) po_des_all_name,4 isheader from (
#                                             SELECT r.req_id,r.product_id,qty_request,product_uom,
#                                                      MAX(CASE WHEN r.rownum = 1 THEN r.price_subtotal ELSE NULL END) AS "vendor1",
#                                                      MAX(CASE WHEN r.rownum = 2 THEN r.price_subtotal ELSE NULL END) AS "vendor2",
#                                                      MAX(CASE WHEN r.rownum = 3 THEN r.price_subtotal ELSE NULL END) AS "vendor3",
#                                                      MAX(CASE WHEN r.rownum = 4 THEN r.price_subtotal ELSE NULL END) AS "vendor4",
#                                                      MAX(CASE WHEN r.rownum = 5 THEN r.price_subtotal ELSE NULL END) AS "vendor5",
#                                                      MAX(CASE WHEN r.rownum = 6 THEN r.price_subtotal ELSE NULL END) AS "vendor6",
# 	                                                 MAX(CASE WHEN r.rownum = 7 THEN r.price_subtotal ELSE NULL END) AS "vendor7",
# 	                                                 MAX(CASE WHEN r.rownum = 8 THEN r.price_subtotal ELSE NULL END) AS "vendor8",
# 	                                                 MAX(CASE WHEN r.rownum = 9 THEN r.price_subtotal ELSE NULL END) AS "vendor9",
# 	                                                 MAX(CASE WHEN r.rownum = 10 THEN r.price_subtotal ELSE NULL END) AS "vendor10"
#                                                 FROM  (select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term,po_des_all_name from (
#                                                   select qcfl_rn.id rownum,company_id,
#                                                     qcfl_rn.req_id,qcfl_rn.partner_id,po_des_all_name,
#                                                     product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from backorder_quotation_comparison_form_line qcfl inner join (
#                                                                 select row_number() over(PARTITION BY req_id
#                                                                             ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
#                                                                             from  backorder_quotation_comparison_form_line
#                                                                             group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
#                                                 )con_qcfl_rn inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id) r
#                                             GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
#                                         )h group by req_id)footer1
#                                         union all
#                                         select * from (
#                                         select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,
#                                         cast(monetary(sum(vendor1)) as varchar) vendor1,cast(monetary(sum(vendor2)) as varchar) vendor2,
#                                         cast(monetary(sum(vendor3)) as varchar) vendor3,cast(monetary(sum(vendor4)) as varchar) vendor4,
#                                         cast(monetary(sum(vendor5)) as varchar) vendor5,
#                                         cast(monetary(sum(vendor6)) as varchar) vendor6,cast(monetary(sum(vendor7)) as varchar) vendor7,
#                                         cast(monetary(sum(vendor8)) as varchar) vendor8,cast(monetary(sum(vendor9)) as varchar) vendor9,
#                                         cast(monetary(sum(vendor10)) as varchar) vendor10,cast('' as varchar) po_des_all_name,5 isheader from (
#                                             SELECT r.req_id,r.product_id,qty_request,product_uom,
#                                                      MAX(CASE WHEN r.rownum = 1 THEN r.price_tax ELSE NULL END) AS "vendor1",
#                                                      MAX(CASE WHEN r.rownum = 2 THEN r.price_tax ELSE NULL END) AS "vendor2",
#                                                      MAX(CASE WHEN r.rownum = 3 THEN r.price_tax ELSE NULL END) AS "vendor3",
#                                                      MAX(CASE WHEN r.rownum = 4 THEN r.price_tax ELSE NULL END) AS "vendor4",
#                                                      MAX(CASE WHEN r.rownum = 5 THEN r.price_tax ELSE NULL END) AS "vendor5",
#                                                      MAX(CASE WHEN r.rownum = 6 THEN r.price_tax ELSE NULL END) AS "vendor6",
#                                                      MAX(CASE WHEN r.rownum = 7 THEN r.price_tax ELSE NULL END) AS "vendor7",
#                                                      MAX(CASE WHEN r.rownum = 8 THEN r.price_tax ELSE NULL END) AS "vendor8",
#                                                      MAX(CASE WHEN r.rownum = 9 THEN r.price_tax ELSE NULL END) AS "vendor9",
#                                                      MAX(CASE WHEN r.rownum = 10 THEN r.price_tax ELSE NULL END) AS "vendor10"
#                                                 FROM  (select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term,po_des_all_name from (
#                                                   select qcfl_rn.id rownum,company_id,po_des_all_name,
#                                                     qcfl_rn.req_id,qcfl_rn.partner_id,
#                                                     product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from backorder_quotation_comparison_form_line qcfl inner join (
#                                                                 select row_number() over(PARTITION BY req_id
#                                                                             ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
#                                                                             from  backorder_quotation_comparison_form_line
#                                                                             group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
#                                                 )con_qcfl_rn inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id) r
#                                             GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
#                                         )h group by req_id)footer2
#                                         union all
#                                         select * from (
#                                         select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,
#                                         cast(monetary(max(vendor1)) as varchar)  vendor1,cast(monetary(max(vendor2)) as varchar)  vendor2,
#                                         cast(monetary(max(vendor3)) as varchar)  vendor3,cast(monetary(max(vendor4)) as varchar)  vendor4,
#                                         cast(monetary(max(vendor5)) as varchar)  vendor5,cast(monetary(max(vendor6)) as varchar)  vendor6,
#                                         cast(monetary(max(vendor7)) as varchar)  vendor7,cast(monetary(max(vendor8)) as varchar)  vendor8,
#                                         cast(monetary(max(vendor9)) as varchar)  vendor9,cast(monetary(max(vendor10)) as varchar)  vendor10,
#                                         cast('' as varchar) po_des_all_name,6 isheader from (
#                                             SELECT r.req_id,r.product_id,qty_request,product_uom,
#                                                      MAX(CASE WHEN r.rownum = 1 THEN r.amount_total ELSE NULL END) AS "vendor1",
#                                                      MAX(CASE WHEN r.rownum = 2 THEN r.amount_total ELSE NULL END) AS "vendor2",
#                                                      MAX(CASE WHEN r.rownum = 3 THEN r.amount_total ELSE NULL END) AS "vendor3",
#                                                      MAX(CASE WHEN r.rownum = 4 THEN r.amount_total ELSE NULL END) AS "vendor4",
#                                                      MAX(CASE WHEN r.rownum = 5 THEN r.amount_total ELSE NULL END) AS "vendor5",
#                                                      MAX(CASE WHEN r.rownum = 6 THEN r.amount_total ELSE NULL END) AS "vendor6",
#                                                      MAX(CASE WHEN r.rownum = 7 THEN r.amount_total ELSE NULL END) AS "vendor7",
#                                                      MAX(CASE WHEN r.rownum = 8 THEN r.amount_total ELSE NULL END) AS "vendor8",
#                                                      MAX(CASE WHEN r.rownum = 9 THEN r.amount_total ELSE NULL END) AS "vendor9",
#                                                      MAX(CASE WHEN r.rownum = 10 THEN r.amount_total ELSE NULL END) AS "vendor10"
#                                                 FROM  (select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,amount_total,price_tax,payment_term_id,incoterm_id,delivery_term,po_des_all_name from (
#                                                   select qcfl_rn.id rownum,company_id,po_des_all_name,
#                                                     qcfl_rn.req_id,qcfl_rn.partner_id,
#                                                     product_id,price_unit,qty_request,product_uom,amount_total,price_tax,payment_term_id,incoterm_id,delivery_term from backorder_quotation_comparison_form_line qcfl inner join (
#                                                                 select row_number() over(PARTITION BY req_id
#                                                                             ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
#                                                                             from  backorder_quotation_comparison_form_line
#                                                                             group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
#                                                 )con_qcfl_rn inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id) r
#                                             GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
#                                         )h group by req_id)footer
#                                         union all
#                                         select * from (
#                                         select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,max(vendor1) vendor1,max(vendor2) vendor2,max(vendor3) vendor3,
#                                         max(vendor4) vendor4,max(vendor5) vendor5,
#                                         max(vendor6) vendor6,max(vendor7) vendor7,
#                                         max(vendor8) vendor8,max(vendor9) vendor9,
#                                         max(vendor10) vendor10,cast('' as varchar) po_des_all_name,7 isheader from (
#                                             SELECT r.req_id,r.product_id,qty_request,product_uom,
#                                                      MAX(CASE WHEN r.rownum = 1 THEN r.name_term ELSE NULL END) AS "vendor1",
#                                                      MAX(CASE WHEN r.rownum = 2 THEN r.name_term ELSE NULL END) AS "vendor2",
#                                                      MAX(CASE WHEN r.rownum = 3 THEN r.name_term ELSE NULL END) AS "vendor3",
#                                                      MAX(CASE WHEN r.rownum = 4 THEN r.name_term ELSE NULL END) AS "vendor4",
#                                                      MAX(CASE WHEN r.rownum = 5 THEN r.name_term ELSE NULL END) AS "vendor5",
#                                                      MAX(CASE WHEN r.rownum = 6 THEN r.name_term ELSE NULL END) AS "vendor6",
#                                                      MAX(CASE WHEN r.rownum = 7 THEN r.name_term ELSE NULL END) AS "vendor7",
#                                                      MAX(CASE WHEN r.rownum = 8 THEN r.name_term ELSE NULL END) AS "vendor8",
#                                                      MAX(CASE WHEN r.rownum = 9 THEN r.name_term ELSE NULL END) AS "vendor9",
#                                                      MAX(CASE WHEN r.rownum = 10 THEN r.name_term ELSE NULL END) AS "vendor10"
#                                                 FROM  (
#                                                 select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,name_term,name_inco,delivery_term,po_des_all_name from (
#                                                   select qcfl_rn.id rownum,company_id,po_des_all_name,
#                                                     qcfl_rn.req_id,qcfl_rn.partner_id,
#                                                     product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from backorder_quotation_comparison_form_line qcfl inner join (
#                                                                 select row_number() over(PARTITION BY req_id
#                                                                             ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
#                                                                             from  backorder_quotation_comparison_form_line
#                                                                             group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
#                                                 )con_qcfl_rn
#                                                 			 inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id
#                                                 			 left join (select apt.id apt_id,name name_term from account_payment_term apt)payterm on con_qcfl_rn.payment_term_id = payterm.apt_id
#                                                 			 left join (select id si_id , name name_inco from stock_incoterms si)incoterm on con_qcfl_rn.incoterm_id = incoterm.si_id
#                                                 			 ) r
#                                             GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
#                                         )h group by req_id)paymentterm
#                                         union all
#                                         select * from (
#                                         select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,max(vendor1) vendor1,max(vendor2) vendor2,
#                                         max(vendor3) vendor3,max(vendor4) vendor4,max(vendor5) vendor5,  max(vendor6) vendor6,max(vendor7) vendor7,
#                                         max(vendor8) vendor8,max(vendor9) vendor9,
#                                         max(vendor10) vendor10,cast('' as varchar) po_des_all_name,8 isheader from (
#                                             SELECT r.req_id,r.product_id,qty_request,product_uom,
#                                                      MAX(CASE WHEN r.rownum = 1 THEN r.delivery_term ELSE NULL END) AS "vendor1",
#                                                      MAX(CASE WHEN r.rownum = 2 THEN r.delivery_term ELSE NULL END) AS "vendor2",
#                                                      MAX(CASE WHEN r.rownum = 3 THEN r.delivery_term ELSE NULL END) AS "vendor3",
#                                                      MAX(CASE WHEN r.rownum = 4 THEN r.delivery_term ELSE NULL END) AS "vendor4",
#                                                      MAX(CASE WHEN r.rownum = 5 THEN r.delivery_term ELSE NULL END) AS "vendor5",
#                                                      MAX(CASE WHEN r.rownum = 6 THEN r.delivery_term ELSE NULL END) AS "vendor6",
#                                                      MAX(CASE WHEN r.rownum = 7 THEN r.delivery_term ELSE NULL END) AS "vendor7",
#                                                      MAX(CASE WHEN r.rownum = 8 THEN r.delivery_term ELSE NULL END) AS "vendor8",
#                                                      MAX(CASE WHEN r.rownum = 9 THEN r.delivery_term ELSE NULL END) AS "vendor9",
#                                                      MAX(CASE WHEN r.rownum = 10 THEN r.delivery_term ELSE NULL END) AS "vendor10"
#                                                 FROM  (
#                                                 select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,name_term,name_inco,delivery_term,po_des_all_name from (
#                                                   select qcfl_rn.id rownum,company_id,po_des_all_name,
#                                                     qcfl_rn.req_id,qcfl_rn.partner_id,
#                                                     product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from backorder_quotation_comparison_form_line qcfl inner join (
#                                                                 select row_number() over(PARTITION BY req_id
#                                                                             ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
#                                                                             from  backorder_quotation_comparison_form_line
#                                                                             group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
#                                                 )con_qcfl_rn
#                                                 			 inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id
#                                                 			 left join (select apt.id apt_id,name name_term from account_payment_term apt)payterm on con_qcfl_rn.payment_term_id = payterm.apt_id
#                                                 			 left join (select id si_id , name name_inco from stock_incoterms si)incoterm on con_qcfl_rn.incoterm_id = incoterm.si_id
#                                                 ) r
#                                             GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
#                                         )h group by req_id)deliverydate
#                                         union all
#                                         select * from (
#                                         select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,max(vendor1) vendor1,max(vendor2) vendor2,
#                                         max(vendor3) vendor3,max(vendor4) vendor4,max(vendor5) vendor5, max(vendor6) vendor6,max(vendor7) vendor7,
#                                         max(vendor8) vendor8,max(vendor9) vendor9,
#                                         max(vendor10) vendor10,cast('' as varchar) po_des_all_name,9 isheader from (
#                                             SELECT r.req_id,r.product_id,qty_request,product_uom,
#                                                      MAX(CASE WHEN r.rownum = 1 THEN r.name_inco ELSE NULL END) AS "vendor1",
#                                                      MAX(CASE WHEN r.rownum = 2 THEN r.name_inco ELSE NULL END) AS "vendor2",
#                                                      MAX(CASE WHEN r.rownum = 3 THEN r.name_inco ELSE NULL END) AS "vendor3",
#                                                      MAX(CASE WHEN r.rownum = 4 THEN r.name_inco ELSE NULL END) AS "vendor4",
#                                                      MAX(CASE WHEN r.rownum = 5 THEN r.name_inco ELSE NULL END) AS "vendor5",
#                                                      MAX(CASE WHEN r.rownum = 6 THEN r.name_inco ELSE NULL END) AS "vendor6",
#                                                      MAX(CASE WHEN r.rownum = 7 THEN r.name_inco ELSE NULL END) AS "vendor7",
#                                                      MAX(CASE WHEN r.rownum = 8 THEN r.name_inco ELSE NULL END) AS "vendor8",
#                                                      MAX(CASE WHEN r.rownum = 9 THEN r.name_inco ELSE NULL END) AS "vendor9",
#                                                      MAX(CASE WHEN r.rownum = 10 THEN r.name_inco ELSE NULL END) AS "vendor10"
#                                                 FROM  (
#                                                 select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,name_term,name_inco,delivery_term,po_des_all_name from (
#                                                   select qcfl_rn.id rownum,company_id,po_des_all_name,
#                                                     qcfl_rn.req_id,qcfl_rn.partner_id,
#                                                     product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from backorder_quotation_comparison_form_line qcfl inner join (
#                                                                 select row_number() over(PARTITION BY req_id
#                                                                             ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
#                                                                             from  backorder_quotation_comparison_form_line
#                                                                             group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
#                                                 )con_qcfl_rn
#                                                 			 inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id
#                                                 			 left join (select apt.id apt_id,name name_term from account_payment_term apt)payterm on con_qcfl_rn.payment_term_id = payterm.apt_id
#                                                 			 left join (select id si_id , name name_inco from stock_incoterms si)incoterm on con_qcfl_rn.incoterm_id = incoterm.si_id
#                                                 			 ) r
#                                             GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
#                                         )h group by req_id)franco
#                                         )vqcf inner join quotation_comparison_form qcf on vqcf.req_id = qcf.requisition_id)qcf_line
#                                         left join
#                                         (select rank_id,product_id,last_price,write_date from(
#         								select row_number() over(PARTITION BY po_id
#                                                                             ORDER BY write_date DESC NULLS LAST) rank_id,* from (
#         								select po.id po_id,order_id,product_id,price_unit last_price,state,write_date  from purchase_order po left join (
#         									select id,order_id,product_id,price_total,price_unit,product_qty from purchase_order_line)pol on po.id = pol.order_id
#         									where state = 'done' group by po.id,order_id,product_id,price_total,price_unit,product_qty )a )b where b.rank_id = 1
#         									)last_price  on qcf_line.product_id = last_price.product_id""")

    #
    # @api.multi
    # @api.depends('qty_request')
    # def _is_grand_total_label(self):
    #     for rec in self :
    #         if rec.isheader == 1:
    #             rec.po_des_all_name = ''
    #             rec.last_price = ''
    #             rec.write_date = ''
    #         elif rec.isheader == 2:
    #             rec.qty_request = 'xxx'
    #             rec.po_des_all_name = ''
    #             rec.write_date = ''
    #         elif rec.isheader == 3:
    #             rec.po_des_all_name = ''+rec.po_des_all_name
    #             rec.grand_total_label = ''
    #             rec.qty_request = str(rec.qty_request)
    #             rec.last_price_char = str(rec.last_price)
    #         elif rec.isheader == 4:
    #             rec.qty_request = 'Sub Total'
    #             rec.po_des_all_name = ''
    #             rec.write_date = ''
    #         elif rec.isheader == 5:
    #             rec.qty_request = 'Tax %'
    #             rec.po_des_all_name = ''
    #             rec.write_date = ''
    #         elif rec.isheader == 6:
    #             rec.qty_request = 'Grand Total'
    #             rec.po_des_all_name = ''
    #             rec.write_date = ''
    #         elif rec.isheader == 7:
    #             rec.qty_request = 'TOP'
    #             rec.po_des_all_name = ''
    #             rec.last_price = ''
    #             rec.write_date = ''
    #         elif rec.isheader == 8:
    #             rec.qty_request = 'Delivery'
    #             rec.po_des_all_name = ''
    #             rec.write_date = ''
    #         elif rec.isheader == 9:
    #             rec.qty_request = 'Incoterm/FRANCO'
    #             rec.po_des_all_name = ''
    #             rec.write_date = ''

class StateProcurementProcess(models.Model):

    _name = 'state.procurement.process'
    _description = 'Tracking State From Purchase Request'
    _auto = False
    _order = 'pr_complete_name desc'


    id = fields.Char('id')
    pr_id = fields.Integer('purchase request')
    date_pr = fields.Date('Purchase Request Date')
    state = fields.Char('Purchase Request state')
    pr_complete_name = fields.Char('Purchase Request Complete Name')
    tender_complete_name = fields.Char('Tender Complete Name')
    tender_state = fields.Char('Tender State')
    qcf_complete_name = fields.Char('Qcf Complete Name')
    qcf_state = fields.Char('Qcf State')
    po_complete_name = fields.Char('Purchase Order Complete Name')
    po_state = fields.Char('Purchase Order State')
    complete_name_picking = fields.Char('GRN Complete Name')
    grn_state = fields.Char('GRN State')

    def init(self, cr):
        drop_view_if_exists(cr, 'state_procurement_process')
        cr.execute(""" create or replace view state_procurement_process as
            select
                row_number() over() id,
                pr.id pr_id,pr.date_start date_pr,
                pr.state state,
                pr.complete_name pr_complete_name,
                tender.complete_name tender_complete_name,
                tender.state tender_state,qcf.complete_name qcf_complete_name,
                qcf.state qcf_state,
                po.complete_name po_complete_name,
                po.state po_state,grn.complete_name_picking,grn.state grn_state from purchase_request pr
            left join (
                select id tender_id,complete_name,origin,state from purchase_requisition
                )tender on pr.complete_name = tender.origin
            left join(
                select id,complete_name,state,origin from quotation_comparison_form
            )qcf on pr.complete_name = qcf.origin
            left join(
                select id,complete_name,state,source_purchase_request from purchase_order
            )po on pr.complete_name = po.source_purchase_request
            left join(
                select id,complete_name_picking,state,pr_source from stock_picking
                    )grn on pr.complete_name = grn.pr_source
                        """)


