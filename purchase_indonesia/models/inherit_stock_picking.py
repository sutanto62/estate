from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re
import json
import logging
from operator import attrgetter
import re


class InheritStockPicking(models.Model):

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
    def _get_requested_purchase_request(self):
        #find Requested Purchase Request
        for item in self:
            request_id = item.purchase_id.request_id.id
            purchase_request = item.env['purchase.request'].search([('id','=',request_id)]).requested_by.id

            return purchase_request


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
    def _get_office_level_id(self):

        try:
            employee = self._get_employee().office_level_id.name
        except:
            raise exceptions.ValidationError('Office level Name Is Null')

        return employee


    _inherit = 'stock.picking'

    complete_name_picking =fields.Char("Complete Name", compute="_complete_name_picking", store=True)
    requested_by = fields.Many2one('res.users',
                                   'Requested by',
                                   required=False,
                                   track_visibility='onchange',compute='_onchange_requested_by'
                                   )
    assigned_to = fields.Many2one('res.users', 'Approver',compute='_onchange_assigned_to',
                                  track_visibility='onchange')
    type_location = fields.Char('Location code')
    location = fields.Char('Location')
    pr_source = fields.Char("Purchase Request Source")
    companys_id = fields.Many2one('res.company','Company')
    code_sequence = fields.Char('Good Receipt Note Sequence')
    purchase_id = fields.Many2one('purchase.order','Purchase Order')
    not_seed = fields.Boolean(compute='_change_not_seed')
    grn_no = fields.Char()
    delivery_number = fields.Char()
    validation_receive = fields.Char()
    validation_manager = fields.Boolean('Validation Manager',compute='_check_validation_manager')
    description = fields.Text('Description')

    _defaults = {
        'not_seed':True,
    }

    @api.multi
    @api.depends('assigned_to')
    def _check_validation_manager(self):
        for item in self:
            if not item.validation_receive:
                item.validation_manager = True if item.assigned_to.id == item._get_user().id else False
            else:
                item.validation_manager = False

    @api.multi
    def action_validate_manager(self):
        for item in self:
            receive_message = 'This GRN / SRN Approved by Manager \"%s\" '%(item.assigned_to.name)
            item.validation_receive = receive_message


    @api.multi
    @api.depends('purchase_id')
    def _onchange_requested_by(self):
        for item in self:
            if item.purchase_id:
                item.requested_by = item._get_requested_purchase_request()

    @api.multi
    @api.depends('requested_by')
    def _onchange_assigned_to(self):
        for item in self:
            if item.requested_by:
                item.assigned_to = item._get_manager_requested_by()

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
        qty = min(item.product_qty for item in self.pack_operation_product_ids)
        done = min(item.qty_done for item in self.pack_operation_product_ids)

        if qty and done < 0:
            self.action_move_picking_force_stop()
            self.write({'state':'done'})
        else :
            super(InheritStockPicking,self).do_transfer()


    @api.multi
    def do_new_transfer(self):
            #update Quantity Received in Purchase Tender after shipping
            po_list = self.env['purchase.order'].search([('id','=',self.purchase_id.id)]).origin

            #search Tender

            tender = self.env['purchase.requisition'].search([('complete_name','like',po_list)]).id

            purchase_requisition_line = self.env['purchase.requisition.line'].search([('requisition_id','=',tender)])

            count_product =0
            count_action_cancel_status =0
            if self._get_user().id != self.requested_by.id:
                error_msg = 'You cannot approve this \"%s\" cause you are not requested this PP '%(self.complete_name_picking)
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
                        if sumitemmin <= 0 :
                            purchase_data = {
                                'state' : 'received_force_done'
                            }
                            po = self.env['purchase.order'].search([('id','=',self.purchase_id.id)]).write(purchase_data)
                        else:
                            purchase_data = {
                                'state' : 'done'
                            }
                            po = self.env['purchase.order'].search([('id','=',self.purchase_id.id)]).write(purchase_data)

                        if stock_pack_operation_length == 1 and sumitemmin < 0 :
                            count_action_cancel_status = count_action_cancel_status +1

                        count_product = count_product +1

                if count_action_cancel_status == count_product :
                    po = self.env['purchase.order'].search([('id','=',self.purchase_id.id)])
                    po.button_cancel()
                    for itemmin in self.pack_operation_product_ids:
                        purchase_requisition_linemin = self.env['purchase.requisition.line'].search([('requisition_id','=',tender),('product_id','=',itemmin.product_id.id)])
                        if itemmin.qty_done < 0 :
                            for recordoutstanding in purchase_requisition_linemin:
                                outstanding_data = {
                                            'qty_outstanding' : itemmin.qty_done * -1
                                        }
                                recordoutstanding.write(outstanding_data)
                    self.action_cancel()
                else:
                    self.do_transfer()

                super(InheritStockPicking,self).do_new_transfer()

    @api.multi
    def print_grn(self):
        return self.env['report'].get_action(self, 'purchase_indonesia.report_goods_receipet_notes_document')



class InheritStockPackOperation(models.Model):

    _inherit='stock.pack.operation'

    @api.multi
    def do_force_donce(self):
        # do force down line stock picking
        compute_product = self.product_qty * -1
        self.product_qty = compute_product
        self.qty_done = compute_product

    @api.multi
    def split_quantities(self):
        #constraint split quantities in stock.pack.operation
        for pack in self:
            if pack.qty_done < 0:
                error = 'Quantity done must be higher than 0 '
                raise exceptions.ValidationError(error)
        super(InheritStockPackOperation,self).split_quantities()




