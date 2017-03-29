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
    def purchase_procurement_staff(self):
        return 'Purchase Request Procurment Staff'

    @api.multi
    def purchase_request_finance(self):
        return 'Purchase Request Finance Procurement'

    _inherit = "stock.picking"

    invoice_count = fields.Integer(compute="_compute_invoice", string='# of Invoices', copy=False, default=0)

    def return_action_to_open(self, cr, uid, ids, context=None):
        """ This opens the xml view specified in xml_id for the current Quotation Comparison """
        if context is None:
            context = {}
        if context.get('xml_id'):
            res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid ,'account', context['xml_id'], context=context)
            res['context'] = context
            stock = self.pool.get('stock.picking')
            stock_partner = stock.search(cr,uid,[('id','=',ids[0])],context=context)
            stock_id = stock.browse(cr,uid,stock_partner)
            partner_id = 0
            purchase_id = 0
            purchase_name = ''
            for item in stock_id:
                partner_id= item.partner_id.id
                purchase_id= item.purchase_id.id
                purchase_name = item.purchase_id.complete_name
            res['context'].update({
                'default_picking_id': ids[0],
                'default_partner_id': partner_id,
                'default_purchase_id':purchase_id,
                'default_origin' : purchase_name,
            })
            res['domain'] = [('picking_id','=', ids[0])]
            return res
        return False

    @api.depends('purchase_id.order_line.invoice_lines.invoice_id.state')
    def _compute_invoice(self):
        for order in self:
            invoices = self.env['account.invoice']
            invoice_id = invoices.search([('picking_id','=',order.id)])
            order.invoice_count = len(invoice_id)

    @api.multi
    def _get_procurement_finance(self):
        #get List of Finance from user.groups
        arrFinancehead = []

        #search User Finance from user list
        listprocurement= self.env['res.groups'].search([('name','like',self.purchase_request_finance())]).users

        for financeproc in listprocurement:
            arrFinancehead.append(financeproc.id)
        try:
            fin_procur = self.env['res.users'].search([('id','=',arrFinancehead[0])]).id
        except:
            raise exceptions.ValidationError('User get Role Finance Procurement Not Found in User Access')

        return fin_procur

    @api.multi
    def _get_procurement_staff(self):
        #get List of Procurement staff from user.groups
        arrFinancestaff = []
        arrProcureId = []

        #search User Finance from user list
        listprocurementstaff= self.env['res.groups'].search([('name','like',self.purchase_procurement_staff())]).users

        for financeproc in listprocurementstaff:
            arrFinancestaff.append(financeproc.id)
        try:
            fin_procur = self.env['res.users'].search([('id','in',arrFinancestaff)])
            for record in fin_procur:
                arrProcureId.append(record.id)
        except:
            raise exceptions.ValidationError('User get Role Finance Procurement Not Found in User Access')

        return self._get_user() in arrProcureId

