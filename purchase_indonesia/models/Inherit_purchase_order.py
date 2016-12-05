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

class InheritPurchaseOrder(models.Model):

    _inherit = 'purchase.order'
    _rec_name = 'complete_name'

    delivery_term = fields.Char('Term Of Delivery')
    companys_id = fields.Many2one('res.company','Company')
    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    type_location = fields.Selection([('KOKB','Estate'),
                                     ('KPST','HO'),('KPWK','RO')],'Location Type')
    source_purchase_request = fields.Char('Source Purchase Request')
    po_no = fields.Char('Purchase order number')
    hide = fields.Boolean('Hide')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
        ], string='Status', readonly=True, select=True, copy=False, default='draft', track_visibility='onchange')

    _defaults = {
        'hide' : False
    }

    @api.one
    @api.depends('name','date_order','companys_id','type_location')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d %H:%M:%S'
        if self.po_no and self.date_order and self.companys_id.code and self.type_location:
            date = self.date_order
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

            self.complete_name = self.po_no + ' / ' \
                                 +str(month) +' / '+str(year)\
                                 +' / '+self.companys_id.code+' / '\
                                 +str(self.type_location)
        elif not self.po_no and self.date_order and self.companys_id.code and self.type_location:
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
            self.complete_name = ' Draft '+self.name  + ' / ' \
                                 +str(month) +' / '+str(year)\
                                 +' / '+self.companys_id.code+' / '+str(self.type_location)

        return True

    @api.multi
    def button_confirm(self):
        super(InheritPurchaseOrder,self).button_confirm()
        self._update_shipping()
        self._update_po_no()
        return True

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
        purchase_data = {
            'po_no' : self.env['ir.sequence'].next_by_code('purchase.po_no')
        }
        po.write(purchase_data)

    @api.multi
    def _update_shipping(self):
        for purchase_order in self:
            purchase_data = {
                'companys_id': purchase_order.companys_id.id,
                'purchase_id': purchase_order.id,
                'type_location': purchase_order.type_location,
                'pr_source' : purchase_order.source_purchase_request,
            }
            self.env['stock.picking'].search([('purchase_id','=',self.id)]).write(purchase_data)
        return True

class InheritPurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    qty_request = fields.Float('Quantity Actual')
    spesification = fields.Text('Spesification')

