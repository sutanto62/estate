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

    _inherit = 'stock.picking'

    complete_name_picking =fields.Char("Complete Name", compute="_complete_name_picking", store=True)
    type_location = fields.Selection([('KOKB','Estate'),
                                     ('KPST','HO'),('KPWK','RO')],'Location Type')
    pr_source = fields.Char("Purchase Request Source")
    companys_id = fields.Many2one('res.company','Company')
    code_sequence = fields.Char('Good Receipt Note Sequence')
    purchase_id = fields.Many2one('purchase.order','Purchase Order')
    not_seed = fields.Boolean(compute='_change_not_seed')

    _defaults = {
        'not_seed':True
    }

    @api.one
    @api.depends('name','min_date','companys_id','type_location')
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

            self.complete_name_picking = ' / ' \
                                 + self.companys_id.code+' - '\
                                 +'GRN'+' / '\
                                 +str(self.type_location)+'/'+str(month)+'/'+str(year)
        else:
            self.complete_name_picking = self.name

        return True

    @api.multi
    @api.depends('pack_operation_product_ids')
    def _change_not_seed(self):
        for record in self:
            for item in record.pack_operation_product_ids:
                if item.product_id.seed == True:
                    record.not_seed = False
                else:
                    record.not_seed = True

    # @api.multi
    # def do_new_transfer(self):
    #     #update Quantity Received in Purchase Tender after shipping
    #     po_list = self.env['purchase.order'].search([('id','=',self.purchase_id.id)]).origin
    #
    #     #search Tender
    #     tender = self.env['purchase.requisition'].search([('complete_name','like',po_list)]).id
    #     purchase_requisition_line = self.env['purchase.requisition.line'].search([('requisition_id','=',tender)])
    #     action_cancel_status = False
    #     for record in purchase_requisition_line:
    #         stock_pack_operation = record.env['stock.pack.operation'].search([('picking_id','=',self.id),('product_id','=',record.product_id.id)])
    #         stock_pack_operation_length = len(stock_pack_operation)
    #
    #         sumitem = 0
    #         sumitemmin = 0
    #         for item in stock_pack_operation:
    #             if item.qty_done > 0:
    #                 sumitem = sumitem + item.qty_done
    #             else:
    #                 sumitemmin = sumitemmin + item.qty_done
    #         tender_line_data = {
    #              'qty_received' : sumitem + record.qty_received,
    #         }
    #         record.write(tender_line_data)
    #
    #         if stock_pack_operation_length == 1 and sumitemmin < 0 :
    #             action_cancel_status = True
    #         else:
    #             action_cancel_status = False
    #
    #     if action_cancel_status == True :
    #         po = self.env['purchase.order'].search([('id','=',self.purchase_id.id)])
    #         po.button_cancel()
    #         self.action_cancel()
    #     else:
    #         self.do_transfer()
    #
    #     super(InheritStockPicking,self).do_new_transfer()
    #     return True

    @api.multi
    def do_new_transfer(self):

        #update Quantity Received in Purchase Tender after shipping
        po_list = self.env['purchase.order'].search([('id','=',self.purchase_id.id)]).origin

        #search Tender

        tender = self.env['purchase.requisition'].search([('complete_name','like',po_list)]).id

        purchase_requisition_line = self.env['purchase.requisition.line'].search([('requisition_id','=',tender)])

        count_product =0

        count_action_cancel_status =0

        for record in purchase_requisition_line:

            stock_pack_operation = record.env['stock.pack.operation'].search([('picking_id','=',self.id),('product_id','=',record.product_id.id)])
            stock_pack_operation_length = len(stock_pack_operation)

            sumitem =0

            sumitemmin =0

            for item in stock_pack_operation:

                if item.qty_done > 0:

                    sumitem = sumitem + item.qty_done

                else:

                    sumitemmin = sumitemmin + item.qty_done

            tender_line_data = {

                'qty_received' : sumitem + record.qty_received,

                }

            record.write(tender_line_data)

            if stock_pack_operation_length == 1 and sumitemmin < 0 :

                count_action_cancel_status = count_action_cancel_status +1

                count_product = count_product +1

        if count_action_cancel_status == count_product :
            po = self.env['purchase.order'].search([('id','=',self.purchase_id.id)])
            po.button_cancel()
            self.action_cancel()

        else:

            self.do_transfer()

        super(InheritStockPicking,self).do_new_transfer()

        return True


class InheritStockPackOperation(models.Model):

    _inherit='stock.pack.operation'

    @api.multi
    def do_force_donce(self):
        compute_product = self.product_qty * -1
        self.product_qty = compute_product
        self.qty_done = compute_product




