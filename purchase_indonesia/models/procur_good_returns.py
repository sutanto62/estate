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
    date_return = fields.Date('Date Return',required=True)
    warehouse_id = fields.Many2one('stock.location','Warehouse',domain=[('usage','=','internal'),
                                                                        ('estate_location','=',False),('name','in',['Stock','stock'])])
    procurement_return_line_ids = fields.One2many('procur.good.returnline','return_id','Goods Return Line')
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
        self.write({'name':"Procurment Good Return %s " %(name)})
        self.write({'state': 'done'})
        return True

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


class ProcurementGoodReturnsLine(models.Model):

    _name = 'procur.good.returnline'
    _description = 'Return good line from user to warehouse'

    return_id = fields.Many2one('procur.good.return','Procurement Good return ID')
    product_id = fields.Many2one('product.product','Product')
    code_product = fields.Char('Product Code')
    uom_id = fields.Many2one('product.uom','UOM')
    request_id = fields.Many2one('procur.good.request','Number Request Good')
    product_qty = fields.Float('Product Quantity')
    code = fields.Char('Account Cost',compute='_change_code')
    block_id = fields.Many2one('estate.block.template', "Block", required=True,
                                  domain=[('estate_location', '=', True), ('estate_location_level', '=', '3')
                                  ,('estate_location_type','=','planted')],compute='_change_block_tt')
    planted_year_id = fields.Many2one('estate.planted.year','Planted Year',compute='_change_block_tt')
    description = fields.Text('Description')

    @api.multi
    @api.onchange('product_id')
    def _onchange_product_id(self):
        arrProduct = []
        if self:
            bpb_line = self.env['procur.good.requestline'].search([])
            for record in bpb_line:
                arrProduct.append(record.product_id.id)
            return {
                'domain':{
                    'product_id':[('id','in',arrProduct)]
                }
            }


    @api.multi
    @api.onchange('product_id')
    def _onchange_request_id(self):
        arrProduct=[]
        for item in self:
            bpb_line = item.env['procur.good.requestline'].search([('product_id','=',item.product_id.id)])
            for record in bpb_line:
                arrProduct.append(record.owner_id)
            return {
                'domain':{
                    'request_id':[('id','in',arrProduct)]
                }
            }

    @api.multi
    @api.depends('product_id','request_id')
    def _change_code(self):
        for item in self:
            bpb_line = item.env['procur.good.requestline'].search([('product_id','=',item.product_id.id),('owner_id','=',item.request_id.id)])
            for record in bpb_line:
                item.code = record.code

    @api.multi
    @api.depends('product_id','request_id')
    def _change_block_tt(self):
        for item in self:
            bpb_line = item.env['procur.good.requestline'].search([('product_id','=',item.product_id.id),('owner_id','=',item.request_id.id)])
            for record in bpb_line:
                item.block_id = record.block_id
                item.planted_year_id= record.planted_year_id
