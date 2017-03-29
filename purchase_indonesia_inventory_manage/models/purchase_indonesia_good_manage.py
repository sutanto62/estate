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

class InheritStockMove(models.Model):

    _inherit = 'stock.move'

    general_account_id = fields.Many2one('account.account','General Account')
    description = fields.Text('Description')

class ManagementGoodRequest(models.Model):

    _name = 'management.good.request'
    _description = 'Management Good Request'

    name = fields.Char()
    manage_good_request_code = fields.Char("GR",store=True)
    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    location_id = fields.Many2one('stock.location','Source Location')
    destination_id = fields.Many2one('stock.location','Destination Location')
    picking_type_id = fields.Many2one('stock.picking.type','Stock Picking Type')
    date_schedule = fields.Date('Date Schedule',required=True)
    requester_id = fields.Many2one('hr.employee','Requester')
    department_id = fields.Many2one('hr.department','Department')
    request_id = fields.Many2one('procur.good.request','Number Request Good')
    company_id = fields.Many2one('res.company','Company')
    warehouse_id = fields.Many2one('stock.location','Source Warehouse',domain=[('usage','=','internal'),
                                                                        ('estate_location','=',False),('name','in',['Stock','stock'])])
    goodrequestline_ids = fields.One2many('management.good.request.line','owner_id','Good Request Line')
    goodreturnline_ids = fields.One2many('management.good.return.line','owner_id','Good Return Line')
    type = fields.Selection([
        ('request', 'Request Goods'),
        ('return', 'Return Goods')
    ],string="Type Request")
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

    @api.multi
    def action_send(self,):
        self.write({'state': 'confirm'})
        return True

    @api.multi
    def action_confirm(self,):
        """ Confirms Good request.
        """
        name = self.name
        self.write({'name':"Management Good Request %s " %(name)})
        self.write({'state': 'done'})
        if self.type == 'request':
            self.action_move()
            self.action_generate_qty_done()

        elif self.type == 'return':
            self.action_move_return()
        return True

    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done', 'date_schedule': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    @api.multi
    def action_reject(self,):
        self.write({'state': 'reject', 'date_request': self.date_schedule})
        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel', 'date_request': self.date_schedule})
        return True

    @api.multi
    def action_move(self):
        #create Stock move From Warehouse To PB
        for item in self.goodrequestline_ids:
            management_line = self.env['management.good.request.line'].search([('product_id','=',item.product_id.id),
                                                               ('owner_id', '=', self.id)
                                                               ])
            for record in management_line:

                move_data = {
                    'product_id': record.product_id.id,
                    'product_uom_qty': record.qty_done,
                    'picking_type_id' : self.picking_type_id.id,
                    'origin':self.origin,
                    'product_uom': record.uom_id.id,
                    'name': record.product_id.name,
                    'date_expected': self.date_schedule,
                    'location_id': self.warehouse_id.id,
                    'location_dest_id': self.destination_id.id,
                    'general_account_id':record.general_account_id.id,
                    'description':record.description,
                    'state': 'confirmed', # set to done if no approval required
                }

                move = self.env['stock.move'].create(move_data)
                move.action_confirm()
                move.action_done()

    @api.multi
    def action_move_return(self):
        #create Stock move From Warehouse To PB
        for item in self.goodreturnline_ids:
            management_line = self.env['management.good.return.line'].search([('product_id','=',item.product_id.id),
                                                               ('owner_id', '=', self.id)
                                                               ])
            for record in management_line:

                move_data = {
                    'product_id': record.product_id.id,
                    'product_uom_qty': record.qty,
                    'picking_type_id' : self.picking_type_id.id,
                    'origin':self.origin,
                    'product_uom': record.uom_id.id,
                    'name': record.product_id.name,
                    'date_expected': self.date_schedule,
                    'location_id':self.destination_id.id ,
                    'location_dest_id': self.warehouse_id.id,
                    'general_account_id':record.general_account_id.id,
                    'description':record.description,
                    'state': 'confirmed', # set to done if no approval required
                }

                move = self.env['stock.move'].create(move_data)
                move.action_confirm()
                move.action_done()


    @api.multi
    def action_generate_qty_done(self):
        for item in self.goodrequestline_ids:
            management_line = self.env['management.good.request.line'].search([('product_id','=',item.product_id.id),
                                                               ('owner_id', '=', self.id)
                                                               ])
            for record in management_line:
                good_request_data = {
                        'qty_done':record.qty_done
                    }
                good_request = self.env['procur.good.request'].search([('complete_name','like',self.origin)]).id
                good_request_line = self.env['procur.good.requestline'].search([('request_id','=',good_request),
                                                                                ('product_id','=',record.product_id.id)]).write(good_request_data)

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

    @api.multi
    @api.onchange('type')
    def _onchange_picking_id(self):
        #onchange picking type ID

        if self.type == 'request':

            return {
                'domain':{
                    'picking_type_id' :[('code','in',['outgoing','internal'])]
                }
            }

        elif self.type == 'return':

            return {
                'domain':{
                    'picking_type_id' :[('code','in',['incoming'])]
                }
            }


class ManagementGoodRequestLine(models.Model):

    _name = 'management.good.request.line'
    _description = 'Management Good Request Line '

    product_id = fields.Many2one('product.product','Product')
    uom_id = fields.Many2one('product.uom','UOM')
    qty = fields.Integer('Quantity Request')
    qty_stock = fields.Integer('Quantity Stock',compute='_change_get_qty_available')
    qty_done = fields.Integer('Quantity Done')
    code = fields.Char('Transaction Code')
    general_account_id = fields.Many2one('account.account','General Account')
    block_id = fields.Many2one('estate.block.template', "Block", required=True,
                                  domain=[('estate_location', '=', True), ('estate_location_level', '=', '3')
                                  ,('estate_location_type','=','planted')])
    planted_year_id = fields.Many2one('estate.planted.year','Planted Year')
    description = fields.Text('Description')
    owner_id = fields.Integer()

    @api.multi
    @api.depends('product_id')
    def _change_get_qty_available(self):
        #get stock from stock quant
        for record in self:
            if record.product_id:
               arrTemp =[]
               location_id = self.env['stock.location'].search([('usage','=','internal')])
               for item in location_id:
                   arrTemp.append(item.id)
               stock_quant_plus = record.env['stock.quant'].search([('product_id','=',record.product_id.id),('negative_move_id','=',None),('location_id','in',arrTemp)])
               stock_quant_min = record.env['stock.quant'].search([('product_id','=',record.product_id.id),('negative_move_id','!=',None),('location_id','in',arrTemp)])
               stock_plus = sum(stock.qty for stock in stock_quant_plus)
               stock_min = sum(stock.qty for stock in stock_quant_min)
               total_quantity = stock_plus + stock_min
               record.qty_stock = total_quantity

    @api.multi
    @api.onchange('product_id')
    def _onchange_uom(self):
        #onchange UOM in Request Good
        if self.product_id:
            self.uom_id = self.product_id.uom_id


class ManagementGoodReturnLine(models.Model):

    _name = 'management.good.return.line'
    _description = 'Management Good Return Line'

    product_id = fields.Many2one('product.product','Product')
    code_product = fields.Char('Product Code')
    uom_id = fields.Many2one('product.uom','UOM')
    qty = fields.Integer('Quantity Return')
    code = fields.Char('Transaction Code')
    general_account_id = fields.Many2one('account.account','General Account')
    block_id = fields.Many2one('estate.block.template', "Block", required=True,
                                  domain=[('estate_location', '=', True), ('estate_location_level', '=', '3')
                                  ,('estate_location_type','=','planted')])
    planted_year_id = fields.Many2one('estate.planted.year','Planted Year')
    description = fields.Text('Description')
    owner_id = fields.Integer()





