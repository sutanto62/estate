from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from openerp import tools


class ManagementGoodRequest(models.Model):

    _name = 'management.good.request'
    _description = 'Management Good Request'

    name = fields.Char()
    manage_good_request_code = fields.Char("GR",store=True)
    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    location_id = fields.Many2one('stock.location','Source Location')
    destination_id = fields.Many2one('stock.location','Destination Location')
    date_schedule = fields.Date('Date Schedule',required=True)
    requester_id = fields.Many2one('hr.employee','Requester')
    department_id = fields.Many2one('hr.department','Department')
    company_id = fields.Many2one('res.company','Company')
    goodrequestline_ids = fields.One2many('management.good.request.line','owner_id','Good Request Line')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Send Request'),
        ('approve', 'Confirm'),
        ('done', 'Done'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled')], string="State",store=True)
    origin = fields.Char('Source Document')
    _defaults = {
        'state' : 'draft'
    }

    #sequence
    def create(self, cr, uid,vals, context=None):
        vals['manage_good_request_code']=self.pool.get('ir.sequence').get(cr, uid,'management.good.request')
        res=super(ManagementGoodRequest, self).create(cr, uid,vals)
        return res

    @api.one
    @api.depends('manage_good_request_code','date_schedule')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d'
        if not self.origin:
            if self.manage_good_request_code and self.date_schedule:
                date = self.date_schedule
                conv_date = datetime.strptime(str(date), fmt)
                month = conv_date.month
                year = conv_date.year
                self.complete_name = self.manage_good_request_code + ' / ' \
                                     + self.department_id.name+' / '\
                                     +self.company_id.name+' / '\
                                     +str(month)+'/'+str(year)
            else:
                self.complete_name = self.name
        if self.origin and self.manage_good_request_code and self.date_schedule:
            self.complete_name = self.origin

        return True

    @api.multi
    @api.onchange('department_id')
    def _onchange_employee_id(self):
        #onchange employee by Department
        arrEmployee=[]
        if self.department_id:

            employee = self.env['hr.employee'].search([('department_id.id','=',self.department_id.id)])
            for employeelist in employee:
                arrEmployee.append(employeelist.id)
            return {
                'domain':{
                    'requester_id' :[('id','in',arrEmployee)]
                }
            }

class ManagementGoodRequestLine(models.Model):

    _name = 'management.good.request.line'
    _description = 'Management Good Request Line '

    product_id = fields.Many2one('product.product','Product')
    uom_id = fields.Many2one('product.uom','UOM')
    qty = fields.Integer('Quantity Request')
    qty_stock = fields.Integer('Quantity Stock')
    qty_done = fields.Integer('Quantity Done')
    owner_id = fields.Integer()

    @api.multi
    @api.onchange('product_id')
    def _onchange_get_qty_available(self):
        #get stock from stock quant
        arrQty=[]
        if self.product_id:
            qty_stock = self.env['stock.quant'].search([('product_id.id','=',self.product_id.id)])
            for stock in qty_stock:
                arrQty.append(stock.qty)
            for Quantity in arrQty:
                qty = float(Quantity)
                self.qty_stock = qty

    @api.multi
    @api.onchange('product_id')
    def _onchange_uom(self):
        #onchange UOM in Request Good
        if self.product_id:
            self.uom_id = self.product_id.uom_id




