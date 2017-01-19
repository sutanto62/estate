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


class ProcurGoodReturns(models.Model):

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

    _name = 'procur.good.return'
    _description = 'Return good from user to warehouse'
    _rec_name = 'complete_name'


    name = fields.Char('name')
    procur_return_code = fields.Char("GR",store=True)
    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    company_id = fields.Many2one('res.company','Company')
    division_id = fields.Many2one('stock.location', "Division", required=True,
                                  domain=[('estate_location', '=', True), ('estate_location_level', '=', '2')])
    picking_type_id = fields.Many2one('stock.picking.type','Stock Picking Type',domain=[('code','in',['outgoing','internal'])])
    requester_id = fields.Many2one('hr.employee','Requester')
    date_return = fields.Date('Date Return',default=fields.Date.context_today,required=True)
    warehouse_id = fields.Many2one('stock.location','Warehouse',domain=[('usage','=','internal'),
                                                                        ('estate_location','=',False),('name','in',['Stock','stock'])])
    procurement_return_line_ids = fields.One2many('procur.good.returnline','return_id','Goods Return Line')
    request_id = fields.Many2one('procur.good.request','Number Request Good',required=True)
    reject_reason = fields.Text('Reject Return')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Send Request'),
        ('approve', 'Confirm'),
        ('done', 'Done'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled')], string="State",store=True)
    _defaults = {
        'state' : 'draft'
    }

    @api.multi
    @api.onchange('company_id')
    def _onchange_company_id(self):

        if self._get_employee().company_id.id:
            self.company_id = self._get_employee().company_id.id

    @api.multi
    @api.onchange('request_id')
    def _onchange_request_id(self):

        if self.request_id.id:
            self.division_id = self.request_id.division_id.id
            self.requester_id = self.request_id.requester_id.id
            self.picking_type_id = self.request_id.picking_type_id.id
            self.warehouse_id = self.request_id.warehouse_id.id

    @api.multi
    @api.onchange('request_id')
    def _onchange_last_request_id(self):
        requestlist = self.env['procur.good.return'].search([])
        arrRequestlist = []
        for item in self:
            for request in requestlist:
                arrRequestlist.append(request.request_id.id)
            return {
                'domain': {'request_id': [('id','not in',arrRequestlist)]}
            }

    #sequence
    def create(self, cr, uid,vals, context=None):
        vals['procur_return_code']=self.pool.get('ir.sequence').get(cr, uid,'procur.good.return')
        res=super(ProcurGoodReturns, self).create(cr, uid,vals)
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
        self.write({'name':"Procurment Good Return %s " %(name),'state': 'done'})
        self.create_good_return()

    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done', 'date_return': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    @api.multi
    def action_reject(self,):
        self.write({'state': 'reject', 'date_return': self.date_return})
        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel', 'date_return': self.date_return})
        return True

    @api.one
    @api.depends('name', 'procur_return_code','date_return')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d'
        if self.procur_return_code and self.company_id and self.date_return:
            date = self.date_return
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
            self.complete_name = self.procur_return_code + ' / ' \
                                 + self.division_id.name+' / '\
                                 +self.company_id.code+' / '\
                                 +str(month)+'/'+str(year)
        else:
            self.complete_name = self.name

        return True

    @api.multi
    def create_good_return(self):
        arrQty = []
        for return_data in self:
            data_return = {
                'picking_type_id':return_data.picking_type_id.id,
                'request_id':return_data.request_id.id,
                'warehouse_id' : return_data.warehouse_id.id,
                'destination_id' : return_data.division_id.id,
                'date_schedule' : return_data.date_return,
                'requester_id' : return_data.requester_id.id,
                'department_id' : return_data.request_id.department_id.id,
                'company_id' : return_data.company_id.id,
                'type' : 'return',
                'state' : 'draft',
                'origin' : return_data.complete_name
            }
            res = self.env['management.good.request'].create(data_return)


        for returnline in self.env['procur.good.returnline'].search([('return_id','=',self.id)]):
            returnline_data = {
                'product_id':returnline.product_id.id,
                'code_product':returnline.code_product,
                'uom_id' : returnline.uom_id.id,
                'qty' : returnline.product_qty,
                'owner_id' : res.id,
                'block_id' : returnline.block_id.id,
                'description': returnline.description,
                'planted_year_id' : returnline.planted_year_id.id,
                'code' :returnline.code
            }
            self.env['management.good.return.line'].create(returnline_data)

        return True

    @api.multi
    @api.constrains('procurement_return_line_ids')
    def _constrains_product_return_id(self):
        self.ensure_one()
        if self.procurement_return_line_ids:
            temp={}
            for part in self.procurement_return_line_ids:
                part_value_name = part.product_id.name
                if part_value_name in temp.values():
                    error_msg = "Product \"%s\" is set more than once " % part_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[part.id] = part_value_name
            return temp


class ProcurementGoodReturnsLine(models.Model):

    _name = 'procur.good.returnline'
    _description = 'Return good line from user to warehouse'

    return_id = fields.Many2one('procur.good.return','Procurement Good return ID')
    product_id = fields.Many2one('product.product','Product')
    code_product = fields.Char('Product Code')
    uom_id = fields.Many2one('product.uom','UOM')

    product_qty = fields.Float('Product Quantity')
    code = fields.Char('Account Cost',compute='_change_code')
    block_id = fields.Many2one('estate.block.template', "Block", required=True,
                                  domain=[('estate_location', '=', True), ('estate_location_level', '=', '3')
                                  ,('estate_location_type','=','planted')],compute='_change_block_tt')
    planted_year_id = fields.Many2one('estate.planted.year','Planted Year',compute='_change_block_tt')
    description = fields.Text('Description')

    @api.multi
    @api.onchange('product_id')
    def _onchange_uom(self):
        #onchange UOM in Request Good
        if self.product_id:
            self.uom_id = self.product_id.uom_id

    @api.multi
    @api.onchange('product_id')
    def _onchange_product_code(self):
        if self.product_id:
            self.code_product = self.product_id.default_code

    @api.multi
    @api.onchange('product_id')
    def _onchange_product_id(self):
        arrProduct = []
        if self:
            bpb_line = self.env['procur.good.requestline'].search([('request_id','=',self.return_id.request_id.id)])
            for record in bpb_line:
                arrProduct.append(record.product_id.id)
            return {
                'domain':{
                    'product_id':[('id','in',arrProduct)]
                }
            }

    @api.multi
    @api.depends('product_id')
    def _change_code(self):
        for item in self:
            bpb_line = item.env['procur.good.requestline'].search([('product_id','=',item.product_id.id),('request_id','=',self.return_id.request_id.id)])
            for record in bpb_line:
                item.code = record.code

    @api.multi
    @api.depends('product_id')
    def _change_block_tt(self):
        for item in self:
            bpb_line = item.env['procur.good.requestline'].search([('product_id','=',item.product_id.id),('request_id','=',self.return_id.request_id.id)])
            for record in bpb_line:
                item.block_id = record.block_id
                item.planted_year_id= record.planted_year_id
