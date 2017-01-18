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


class ProcurGoodRequest(models.Model):

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
    def _get_user_manager(self):
        #Find Employee user Manager
        employeemanager = self.env['hr.employee'].search([('user_id','=',self._get_user().id)]).parent_id.id
        assigned_manager = self.env['hr.employee'].search([('id','=',employeemanager)]).user_id.id

        return assigned_manager

    _name = 'procur.good.request'
    _description = 'Request good from user to warehouse'
    _rec_name = 'complete_name'

    name = fields.Char('name')
    procur_request_code = fields.Char("GR",store=True)
    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    company_id = fields.Many2one('res.company','Company')
    division_id = fields.Many2one('stock.location', "Division", required=True,
                                  domain=[('estate_location', '=', True), ('estate_location_level', '=', '2')])
    picking_type_id = fields.Many2one('stock.picking.type','Stock Picking Type',domain=[('code','in',['outgoing','internal'])])
    warehouse_id = fields.Many2one('stock.location','Warehouse',domain=[('usage','=','internal'),
                                                                        ('estate_location','=',False),('name','in',['Stock','stock'])])
    department_id = fields.Many2one('hr.department','Department')
    requester_id = fields.Many2one('hr.employee','Requester')
    date_request = fields.Date('Date Request',default=fields.Date.context_today,required=True)
    reject_reason = fields.Text('Reject Reason')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Send Request'),
        ('approve', 'Confirm'),
        ('done', 'Done'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled')], string="State",store=True)
    procur_request_line_ids = fields.One2many('procur.good.requestline','request_id','Procur Good Request Line')
    _defaults = {
        'state' : 'draft'
    }

    @api.multi
    @api.onchange('company_id')
    def _onchange_company_id(self):

        if self._get_employee().company_id.id:
            self.company_id = self._get_employee().company_id.id

    #sequence
    def create(self, cr, uid,vals, context=None):
        vals['procur_request_code']=self.pool.get('ir.sequence').get(cr, uid,'procur.good.request')
        res=super(ProcurGoodRequest, self).create(cr, uid,vals)
        return res

    @api.multi
    def action_send(self,):
        self.write({'state': 'confirm'})
        return True

    @api.multi
    def action_confirm(self,):
        """ Confirms Good request.
        """
        name = self.name
        self.write({'name':"Procurment Good Request %s " %(name)})
        self.write({'state': 'done'})
        self.create_good_request()
        return True

    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done', 'date_request': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    @api.multi
    def action_reject(self,):
        self.write({'state': 'reject', 'date_request': self.date_request})
        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel', 'date_request': self.date_request})
        return True

    @api.multi
    def create_good_request(self):
        arrQty = []
        for request in self:
            request_data = {
                'picking_type_id':request.picking_type_id.id,
                'warehouse_id' : request.warehouse_id.id,
                'destination_id' : request.division_id.id,
                'date_schedule' : request.date_request,
                'requester_id' : request.requester_id.id,
                'department_id' : request.department_id.id,
                'company_id' : request.company_id.id,
                'type' : 'request',
                'state' : 'draft',
                'origin' : request.complete_name
            }
            res = self.env['management.good.request'].create(request_data)


        for requestline in self.env['procur.good.requestline'].search([('request_id','=',self.id)]):
            requestline_data = {
                'product_id':requestline.product_id.id,
                'uom_id' : requestline.uom_id.id,
                'qty' : requestline.qty,
                'owner_id' : res.id,
                'block_id' : requestline.block_id.id,
                'description': requestline.description,
                'planted_year_id' : requestline.planted_year_id.id,
                'code' :requestline.code
            }
            self.env['management.good.request.line'].create(requestline_data)

        return True

    @api.one
    @api.depends('name', 'procur_request_code','date_request')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d'
        if self.procur_request_code and self.company_id and self.date_request:
            date = self.date_request
            conv_date = datetime.strptime(str(date), fmt)
            month = conv_date.month
            year = conv_date.year
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
            self.complete_name = self.procur_request_code + ' / ' \
                                 + self.division_id.name+' / '\
                                 +self.company_id.code+' / '\
                                 +str(month)+'/'+str(year)
        else:
            self.complete_name = self.name

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


class ProcurGoodRequestLine(models.Model):

    _name = 'procur.good.requestline'
    _description = 'Line of Procur Good Request'

    product_id = fields.Many2one('product.product','Product')
    request_id = fields.Many2one('procur.good.request','Request Id')
    uom_id = fields.Many2one('product.uom','UOM')
    qty = fields.Integer('Quantity Request')
    qty_done = fields.Integer('Quantity Actual')
    code = fields.Char('Transaction Code')
    block_id = fields.Many2one('estate.block.template', "Block", required=True,
                                  domain=[('estate_location', '=', True), ('estate_location_level', '=', '3')
                                  ,('estate_location_type','=','planted')])
    planted_year_id = fields.Many2one('estate.planted.year','Planted Year')
    description = fields.Text('Description')
    owner_id = fields.Integer()

    @api.multi
    @api.onchange('product_id')
    def _onchange_uom(self):
        #onchange UOM in Request Good
        if self.product_id:
            self.uom_id = self.product_id.uom_id

    @api.multi
    @api.onchange('block_id')
    def _onchange_planted_year_id(self):
        #onchange Planted year
        if self.block_id:
            self.planted_year_id = self.block_id.planted_year_id

    @api.multi
    @api.onchange('request_id','product_id')
    def _onchange_product_purchase_request_line(self):
        #use to onchange domain product same as product_category
        if self.request_id.department_id:
            arrProductCateg = []
            mappingFuntional = self.env['mapping.department.product'].search([('department_id.id','=',self.request_id.department_id.id)])

            for productcateg in mappingFuntional:
                arrProductCateg.append(productcateg.product_category_id.id)

            arrProdCatId = []
            prod_categ = self.env['product.category'].search([('parent_id','in',arrProductCateg)])

            for productcategparent in prod_categ:
                arrProdCatId.append(productcategparent.id)

            if prod_categ:
                return  {
                    'domain':{
                        'product_id':[('categ_id','in',arrProdCatId)]
                         }
                    }
            elif prod_categ != ():
                return  {
                    'domain':{
                        'product_id':[('categ_id','in',arrProductCateg)]
                         }
                    }



