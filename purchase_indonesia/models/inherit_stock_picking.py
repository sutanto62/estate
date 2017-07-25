from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re
import json
import logging
import time
from operator import attrgetter
import re


class InheritStockPicking(models.Model):

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
    def purchase_request_estate_manager(self):
        return self.env.ref('estate.group_manager', False).id

    @api.multi
    def get_purchase_procurement_staff(self):
        return self.env.ref('purchase_request.group_purchase_request_procstaff', False).id

    @api.multi
    def get_stock_manager(self):
        return self.env.ref('stock.group_stock_manager',False).id

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
    def _get_estate_manager(self):
        #get List of Estate Manager from user.groups
        #Estate Manager

        arrEstateManager = []
        arrAgronomy = []

        estate_manager = self.env['res.groups'].search([('id','=',self.purchase_request_estate_manager())]).users
        technical_agronomy = self.env['res.groups'].search([('id','=',self.purchase_request_technical4())]).users

        for estate in estate_manager:
            arrEstateManager.append(estate.id)
        for deptgroupsrecord in technical_agronomy:
            arrAgronomy.append(deptgroupsrecord.id)

        try:
            manager_estate = self.env['res.users'].search([('id','in',arrEstateManager),('id','in',arrAgronomy)]).id
        except:
            raise exceptions.ValidationError('User Role Estate Manager Not Found in User Access')

        return manager_estate

    @api.multi
    def _get_stock_manager(self):
        #get List of Stock Manager from user.groups
        #Stock Manager

        arrStockManager = []

        stock_manager = self.env['res.groups'].search([('id','=',self.get_stock_manager())]).users


        for stock in stock_manager:
            arrStockManager.append(stock.id)

        try:
            manager_stock = self.env['res.users'].search([('id','in',arrStockManager)],limit = 1).id
        except:
            raise exceptions.ValidationError('User Role Estate Manager Not Found in User Access')

        return manager_stock

    @api.multi
    def _get_user_procurement_staff(self):
        #get List of Procurement Staff from user.groups
        arrProcurement = []
        arrUser = []

        list_procurement = self.env['res.groups'].search([('id','=',self.get_purchase_procurement_staff())]).users

        for procurement in list_procurement:
                arrProcurement.append(procurement.id)
        try:
            staff = self.env['res.users'].search([('id','in',arrProcurement)])

            for user in staff:
                arrUser.append(user.id)
        except:
            raise exceptions.ValidationError('User get Role Procurement Staff Not Found in User Access')

        return arrUser

    @api.multi
    def _get_requested_purchase_request(self):
        #find Requested Purchase Request
        for item in self:
            request_id = item.purchase_id.request_id.id
            purchase_request = item.env['purchase.request'].search([('id','=',request_id)]).requested_by.id

            return purchase_request

    @api.multi
    def _get_department_code(self):
        department_code = []
        for item in self:
            department = item.env['hr.department'].search([])
            for record in department:
                if record.code != 'ICT' and record.code:
                    department_code.append(record.code)
        return department_code

    @api.multi
    def _get_technical_user_id(self):
        for item in self:
            """
                Get Technical user by code company.

                Code :
                    KOKB : Kantor KEBUN
                    KPST : Kantor PUSAT
            """

            technic_user_id = 0
            purchase_request = item.env['purchase.request'].search([('id','=',item._get_purchase_request_id())])

            if purchase_request.code == 'KOKB' :

                if purchase_request.type_functional == 'general' and purchase_request.department_id.code in item._get_department_code():
                    technic_user_id = item._get_manager_requested_by()
                elif purchase_request.type_functional == 'general' and purchase_request.department_id.code == 'ICT':
                    technic_user_id = purchase_request._get_technic_ict()
                elif purchase_request.type_functional == 'technic':
                    technic_user_id = item._get_stock_manager()
                elif purchase_request.type_functional == 'agronomy':
                    technic_user_id = item._get_stock_manager()

            elif purchase_request.code == 'KPST' :

                if purchase_request.type_functional == 'general' and purchase_request.department_id.code in item._get_department_code():
                    technic_user_id = item._get_manager_requested_by()
                elif purchase_request.type_functional == 'general' and purchase_request.department_id.code == 'ICT':
                    technic_user_id = purchase_request._get_technic_ict()
                elif purchase_request.type_functional == 'technic':
                    technic_user_id = purchase_request._get_technic_ie()
                elif purchase_request.type_functional == 'agronomy':
                    technic_user_id = item._get_estate_manager()

            return technic_user_id

    @api.multi
    def _get_manager_requested_by(self):
        #find Manager to approved:
        try:
            employeemanager = self.env['hr.employee'].search([('user_id','=',self._get_requested_purchase_request())]).parent_id.id
            assigned_manager = self.env['hr.employee'].search([('id','=',employeemanager)]).user_id.id
        except:
            raise exceptions.ValidationError('Please Contact your HR Admin to fill your manager')

        if not assigned_manager:
            raise exceptions.ValidationError('Please Contact your HR Admin to fill your manager')

        return assigned_manager

    @api.multi
    def _get_user_purchase_tender(self):
        for item in self :
            arrUser = []

            pr = item.env['purchase.request']
            pr_id = pr.search([('complete_name','like',item.pr_source)]).id
            tender = item.env['purchase.requisition']
            tender_id = tender.search([('request_id','=',pr_id)])

            for record in tender_id:
                arrUser.append(record.user_id.id)

            return arrUser

    @api.multi
    def _get_office_level_id(self):

        try:
            employee = self._get_employee().office_level_id.name
        except:
            raise exceptions.ValidationError('Office level Name Is Null')

        return employee

    @api.multi
    def _get_purchase_request_id(self):
        for item in self:

            purchase_request = item.env['purchase.request']
            purchase_request_id = purchase_request.search([('complete_name','like',item.pr_source)]).id

            return purchase_request_id

    _inherit = 'stock.picking'

    complete_name_picking =fields.Char("Complete Name", compute="_complete_name_picking", store=True)
    requested_by = fields.Many2one('res.users',
                                   'Requested by',
                                   required=False,
                                   track_visibility='onchange',compute='_onchange_requested_by'
                                   )
    assigned_to = fields.Many2one('res.users', 'Approver',
                                  track_visibility='onchange',readonly=1)
    type_location = fields.Char('Location code')
    location = fields.Char('Location')
    pr_source = fields.Char("Purchase Request Source")
    companys_id = fields.Many2one('res.company','Company')
    code_sequence = fields.Char('Good Receipt Note Sequence')
    purchase_id = fields.Many2one('purchase.order','Purchase Order',store=True)
    not_seed = fields.Boolean(compute='_change_not_seed')
    grn_no = fields.Char()
    delivery_number = fields.Char()
    shipper_by = fields.Char('Shipper By',compute='_compute_default_shipper')
    validation_receive = fields.Char()
    validation_manager = fields.Boolean('Validation Manager')
    validation_user = fields.Boolean('Validation User',compute='_check_validation_user')
    validation_check_approve = fields.Boolean('Validation checking approve',compute='_check_validation_manager')
    validation_procurement = fields.Boolean('Validation Procurement')
    description = fields.Text('Description')
    pack_operation_product_ids = fields.One2many('stock.pack.operation', 'picking_id', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, domain=[('product_id', '!=', False),('checking_split','=',False)], string='Non pack')
    purchase_order_name = fields.Char('Purchase Order Complete Name',related='purchase_id.complete_name',store=True)

    _defaults = {
        'not_seed':True,
    }

    @api.multi
    @api.depends('assigned_to')
    def _check_validation_manager(self):
        for item in self:
            if item.validation_manager == True:
                item.validation_check_approve = True if item.assigned_to.id == item._get_user().id  and item.state != 'done' else False
            elif item.validation_manager == True and item.validation_receive and item.state == 'done':
                item.validation_check_approve = False

    @api.multi
    @api.depends('requested_by')
    def _check_validation_user(self):
        for item in self:
            if item.validation_procurement ==  True:
                if item.validation_manager == False and item.state != 'done':
                    item.validation_user = True if item.requested_by.id == item._get_user().id else False
                else:
                    item.validation_user = False
            else:
                item.validation_user = False


    @api.multi
    def action_validate_manager(self):
        for item in self:
            receive_message = 'This GRN / SRN Approved by Manager \"%s\" '%(item.assigned_to.name)
            item.validation_receive = receive_message

    @api.multi
    @api.depends('pr_source')
    def _compute_default_shipper(self):
        for item in self:
            if item.pr_source:
                pr = item.env['purchase.request']
                pr_id = pr.search([('complete_name','like',item.pr_source)]).id
                tender = item.env['purchase.requisition']
                tender_id = tender.search([('request_id','=',pr_id)])
                user = ''
                for record in tender_id:
                    user = record.user_id.name
                item.shipper_by = user

    @api.multi
    def set_qty_done_to_zero(self):
        for item in self:
            data = {
                    'qty_done' : 0
                   }
            item.env['stock.pack.operation'].search([('picking_id','=',item.id)]).write(data)

    @api.multi
    def action_validate_procurement(self):
        for item in self:
            arrProduct = []

            pack_operation = item.env['stock.pack.operation']

            temp_qty_done= 0

            for record in item.pack_operation_product_ids:
                 if item._get_user().id not in list(item._get_user_procurement_staff()) and item._get_user().id not in item._get_user_purchase_tender() :
                        error_msg = 'You cannot approve this \"%s\" , you are not PROCUREMENT STAFF '%(self.complete_name_picking)

                        raise exceptions.ValidationError(error_msg)
                 else:
                     if record.qty_done > 0 or record.qty_done < 0 :
                         temp_qty_done = temp_qty_done + 1

                     if temp_qty_done == 0:
                        error_msg='You cannot Process this \"%s\" , Please Insert Qty Done '%(item.complete_name_picking)
                        raise exceptions.ValidationError(error_msg)

                     else:
                        pack_ids = pack_operation.search([('picking_id','=',item.id),('qty_done','>',0)])

                        for pack in pack_ids:
                            arrProduct.append(pack.product_id.id)

                        picking_pack_ids = pack_operation.search([('picking_id','=',item.id),('product_id','in',arrProduct)])

                        for product in picking_pack_ids:
                            data = {
                                'procurment_qty' : product.qty_done,
                                }
                            product.write(data)

            item.set_qty_done_to_zero()

            #set to Approval User
            item.write({'validation_procurement' : True})

            #send Mail to Approval User
            item.send_mail_template_user()


    @api.multi
    def action_validate_user(self):
        for item in self:

            temp_qty_done= 0

            for record in item.pack_operation_product_ids:
                if record.qty_done > 0 or record.qty_done < 0:
                         temp_qty_done = temp_qty_done + 1

                if temp_qty_done == 0:
                    error_msg='You cannot Process this \"%s\" , Please Insert Qty Done '%(item.complete_name_picking)
                    raise exceptions.ValidationError(error_msg)
                else:
                    if record.qty_done > 0 and record.qty_done < record.product_qty:
                        #show wizard Split quantity
                        wizard_form = item.env.ref('purchase_indonesia.view_stock_picking_split', False)
                        view_id = item.env['stock.picking.wizard.split']
                        vals = {
                                    'name'   : 'this is for set name',
                                }
                        new = view_id.create(vals)
                        return {
                                    'name'      : _('Split Your Delivery Quantity List'),
                                    'type'      : 'ir.actions.act_window',
                                    'res_model' : 'stock.picking.wizard.split',
                                    'res_id'    : new.id,
                                    'view_id'   : wizard_form.id,
                                    'view_type' : 'form',
                                    'view_mode' : 'form',
                                    'target'    : 'new'
                                }
                    elif record.qty_done == record.product_qty:
                        item._get_technical_user_id()
                        item.write({
                            'validation_manager':True,
                            'assigned_to':item._get_technical_user_id()
                        })

                    item.send_mail_template()

    @api.multi
    @api.depends('purchase_id')
    def _onchange_requested_by(self):
        for item in self:
            if item.purchase_id:
                item.requested_by = item._get_requested_purchase_request()

    @api.one
    @api.depends('grn_no','min_date','companys_id','type_location')
    def _complete_name_picking(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d %H:%M:%S'

        if self.min_date and self.companys_id.code and self.type_location:
            date = self.min_date
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

            self.complete_name_picking = self.grn_no +'/' \
                                 + self.companys_id.code+'-'\
                                 +'GRN'+'/'\
                                 +str(self.type_location)+'/'+str(month)+'/'+str(year)
        else:
            self.complete_name_picking = self.name

        return True

    @api.multi
    @api.depends('pack_operation_product_ids')
    def _change_not_seed(self):
        #onchange Record not seed
        for record in self:
            for item in record.pack_operation_product_ids:
                if item.product_id.seed == True:
                    record.not_seed = False
                else:
                    record.not_seed = True

    @api.multi
    def action_move_picking_force_stop(self):
        po_list = self.env['purchase.order'].search([('id','=',self.purchase_id.id)]).origin

        #search Tender

        tender = self.env['purchase.requisition'].search([('complete_name','like',po_list)]).id

        purchase_requisition_line = self.env['purchase.requisition.line'].search([('requisition_id','=',tender)])

        #create Stock move From Purchase to warehouse
        for item in purchase_requisition_line:
            #search Pack Operation Ids
            pack_operation_line = self.env['stock.pack.operation'].search([('picking_id','=',self.id),
                                                                       ('product_id','=',item.product_id.id)
                                                               ])

            stock_move = self.env['stock.move'].search([('origin','=',self.purchase_id.name),
                                                        ('product_id','=',item.product_id.id)])

            quantity_move = sum(record.qty_done for record in pack_operation_line if record.qty_done > 0)

            for record in pack_operation_line:

                move_data = {
                    'product_uom_qty': quantity_move,
                }

                stock_move.write(move_data)
                stock_move.action_confirm()
                stock_move.action_done()


    @api.multi
    def do_transfer(self):
        for item in self:
            #search list of pack operation
            pack_operation = item.env['stock.pack.operation'].search([('picking_id','=',self.id)])

            #search minimal quantity product qty and qty done
            qty = min(item.product_qty for item in pack_operation)
            done = min(item.qty_done for item in pack_operation)

            super(InheritStockPicking,item).do_transfer()

            purchase_order = item.env['purchase.order'].search([('id','=',self.purchase_id.id)])

            sequence_name = 'stock.srn.seq.'+item.type_location.lower()+'.'+item.companys_id.code.lower() if purchase_order.validation_srn == True else 'stock.grn.seq.'+item.type_location.lower()+'.'+item.companys_id.code.lower()

            purchase_data_srn = {
                    'pr_source' : purchase_order.request_id.complete_name,
                    'srn_no' : item.env['ir.sequence'].next_by_code(sequence_name),
                    'assigned_to' : None,
                    'validation_manager':False,
                    'validation_procurement':False,
                    'purchase_order_name':purchase_order.complete_name
                    }
            purchase_data = {
                    'pr_source' : purchase_order.request_id.complete_name,
                    'grn_no' : item.env['ir.sequence'].next_by_code(sequence_name),
                    'assigned_to' : None,
                    'validation_manager':False,
                    'validation_procurement':False,
                    'purchase_order_name':purchase_order.complete_name
                }

            picking = item.env['stock.picking']
            backorder_picking = picking.search([('backorder_id','=',item.id)])
            purchase_state = {'state' : 'received_force_done'}

            if qty and done < 0:
                purchase_order.write(purchase_state)
                # method to use if you want not create back order
                # self.action_move_picking_force_stop()

                if purchase_order.validation_srn == True :
                    backorder_picking.write(purchase_data_srn)
                else:
                    backorder_picking.write(purchase_data)
            else:
                purchase_order.write({'state':'done'})

    @api.multi
    def do_new_transfer(self):
            arrOutstanding = []

            #update Quantity Received in Purchase Tender after shipping
            po_list = self.env['purchase.order'].search([('id','=',self.purchase_id.id)]).origin

            #search Tender
            list_tender = self.env['purchase.requisition']
            search_tender = list_tender.search([('complete_name','=',po_list)])
            tender_id = search_tender.id

            purchase_requisition_line = self.env['purchase.requisition.line'].search([('requisition_id','=',tender_id)])

            requisition_line = self.env['purchase.requisition.line']

            domain = [('requisition_id','=',tender_id),('qty_outstanding','>',0)]

            count_product =0
            count_action_cancel_status =0
            if self._get_user().id != self.assigned_to.id:
                error_msg = 'You cannot approve this \"%s\" , you are not requester of this PP '%(self.complete_name_picking)
                raise exceptions.ValidationError(error_msg)
            else:



                for record in purchase_requisition_line:
                    stock_pack_operation = record.env['stock.pack.operation'].search([('picking_id','=',self.id),('product_id','=',record.product_id.id)])
                    stock_pack_operation_length = len(stock_pack_operation)

                    if stock_pack_operation_length > 0 :
                        sumitem =0

                        sumitemmin =0

                        for item in stock_pack_operation:
                            if item.product_id.type in ['service','consu','product']:
                                if item.qty_done > 0:
                                    sumitem = sumitem + item.qty_done
                                else:
                                    sumitemmin = sumitemmin + item.qty_done
                        tender_line_data = {

                            'qty_received' : sumitem + record.qty_received,
                            'qty_outstanding' : record.product_qty - sumitem if record.qty_received == 0 else record.qty_outstanding - sumitem
                            }
                        record.write(tender_line_data)

                        if stock_pack_operation_length == 1 and sumitemmin < 0 :
                            count_action_cancel_status = count_action_cancel_status +1

                        count_product = count_product +1

                if count_action_cancel_status == count_product :
                    po = self.env['purchase.order'].search([('id','=',self.purchase_id.id)])
                    if self.checking_picking_backorder() == False:
                        po.button_cancel()
                        for itemmin in self.pack_operation_product_ids:
                            purchase_requisition_linemin = self.env['purchase.requisition.line'].search([('requisition_id','=',tender_id),('product_id','=',itemmin.product_id.id)])
                            if itemmin.qty_done < 0 :
                                for recordoutstanding in purchase_requisition_linemin:
                                    outstanding_data = {
                                                'qty_outstanding' : itemmin.qty_done * -1
                                            }
                                    recordoutstanding.write(outstanding_data)


                        self.action_cancel()
                        self.action_validate_manager()
                        self.validation_manager = False
                    else:
                        for itemmin in self.pack_operation_product_ids:
                            purchase_requisition_linemin = self.env['purchase.requisition.line'].search([('requisition_id','=',tender_id),('product_id','=',itemmin.product_id.id)])
                            if itemmin.qty_done < 0 :
                                for recordoutstanding in purchase_requisition_linemin:
                                    outstanding_data = {
                                                'qty_outstanding' : itemmin.qty_done * -1
                                            }
                                    recordoutstanding.write(outstanding_data)

                        self.action_cancel()
                        self.action_validate_manager()
                        self.validation_manager = False
                else:

                    self.do_transfer()
                    self.action_validate_manager()



                super(InheritStockPicking,self).do_new_transfer()

                for outstanding in requisition_line.search(domain):
                    arrOutstanding.append(outstanding.id)

                search_tender.write({
                                'state': 'open' if len(arrOutstanding) > 0 else 'done'
                            })


    @api.multi
    def checking_picking_backorder(self):
        for item in self:
            if not item.backorder_id.id:
                vals = False
            else:
                vals = True
            return vals

    @api.multi
    def print_grn(self):
        if self.state != 'done':
            error_msg = 'You can not print GRN / SRN before status is Done'
            raise exceptions.ValidationError(error_msg)
        return self.env['report'].get_action(self, 'purchase_indonesia.report_goods_receipet_notes_document')

    @api.multi
    @api.constrains('pack_operation_product_ids')
    def _constraint_pack_operation_product_ids(self):
        for item in self:
            if item._get_user().id != item.requested_by.id and item._get_user().id not in list(item._get_user_procurement_staff()):
                error_msg = 'You cannot Process this \"%s\" , You are not requester of this PP or You are not Procurement Staff '%(item.complete_name_picking)
                raise exceptions.ValidationError(error_msg)

    #Email Template Code Starts Here

    @api.one
    def send_mail_template(self):

            # Find the e-mail template
            template = self.env.ref('purchase_indonesia.email_template_stock_picking')
            # You can also find the e-mail template like this:
            # template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
            # Send out the e-mail template to the user
            self.env['mail.template'].browse(template.id).send_mail(self.id,force_send=True)

    @api.one
    def send_mail_template_user(self):
        # Find the e-mail template
        template = self.env.ref('purchase_indonesia.email_template_stock_picking_2')
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


class InheritStockPackOperation(models.Model):

    _inherit='stock.pack.operation'

    checking_split = fields.Boolean('Checking Split',default=False)
    initial_qty = fields.Float('Initial Qty',readonly=1)
    procurment_qty = fields.Float('Procurement Qty',readonly=1,help="Procurement Received QTY From Vendor")

    @api.multi
    def do_force_donce(self):
        # do force down line stock picking
        compute_product = self.product_qty * -1
        self.product_qty = compute_product
        self.qty_done = compute_product


    def split_quantities2(self, cr, uid, ids, context=None):
        for pack in self.browse(cr, uid, ids, context=context):
            if pack.product_qty - pack.qty_done > 0.0 and pack.qty_done < pack.product_qty:
                pack2 = self.copy(cr, uid, pack.id,
                                  default={
                                        'qty_done': 0.0,
                                        'product_qty': pack.product_qty - pack.qty_done,
                                        'checking_split':True,
                                        'initial_qty':pack.product_qty}, context=context)
                copy_pack = pack.env['stock.pack.operation'].search([('id','=',pack2)])
                copy_pack.do_force_donce()
                self.write(cr, uid, [pack.id], {'initial_qty':pack.product_qty,'product_qty': pack.qty_done}, context=context)
            if pack.qty_done < 0:
                error = 'Quantity done must be higher than 0 '
                raise exceptions.ValidationError(error)

        return True




