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

class InheritStockPicking(models.Model):

    _inherit = 'stock.picking'


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


