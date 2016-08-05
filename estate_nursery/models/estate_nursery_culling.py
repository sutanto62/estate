from openerp import models, fields, api, exceptions
import logging
from datetime import datetime, date
from dateutil.relativedelta import *
from openerp.exceptions import ValidationError
import calendar

_logger = logging.getLogger(__name__)
class Culling(models.Model):

    _name = "estate.nursery.culling"
    _description = "Seed Batch Culling"
    _inherit = ['mail.thread']

    name=fields.Char("Culling Name")
    culling_code=fields.Char("LBP")
    partner_id=fields.Many2one('res.partner')
    cullinglineall_ids=fields.One2many('estate.nursery.cullingline','culling_id',"Culling")
    cullingline_ids=fields.One2many('estate.nursery.cullinglinebatch','culling_id',"Culling")
    culling_date = fields.Date("Culling date",store=True,required=True)
    location_type=fields.Many2one('stock.location',("location Last"),domain=[('name','=','Inventory loss'),
                                                                             ('usage','=','inventory'),
                                                                             ],store=True,required=True)
    stockquant_id=fields.Many2one('stock.quant',
                                  domain=[('location_id.estate_location_type', '=', 'nursery'),
                                          ('location_id.scrap_location','=',True),
                                          ('location_id.estate_location_level', '=', '3')],store=True)
    quantitytotal_abnormal = fields.Integer("Quantity Total Abnormal",compute='_compute_total_batch',store=True)
    total_quantityabnormal_temp=fields.Integer(compute='_compute_total_abnormal',store=True)
    total_qtyabnormal=fields.Integer(store=True)
    culling_location_id = fields.Many2one('estate.block.template',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),
                                                  ('scrap_location', '=', True)]
                                          ,store=True)
    selectionform=fields.Selection([('0','None'),('1','Batch'),('2','Selection')],default='0',required=True)
    state= fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),('approved1','First Approval '),('approved2','Second Approval'),('approved3','Third Approval'),
        ('done', 'Done')],string="Culling State")

    #Auto Generated Code of culling
    def create(self, cr, uid, vals, context=None):
        vals['culling_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.culling')
        res=super(Culling, self).create(cr, uid, vals)
        return res

    #calculate Culling Line
    @api.one
    @api.depends('cullingline_ids')
    def _compute_total_batch(self):
        self.quantitytotal_abnormal = 0
        for item in self.cullingline_ids:
            self.quantitytotal_abnormal += item.qty_abnormal_batch
        return True

    @api.one
    @api.depends('cullinglineall_ids')
    def _compute_total_abnormal(self):
        self.total_quantityabnormal_temp = 0
        for a in self.cullinglineall_ids:
            self.total_quantityabnormal_temp += a.qty_abnormal_selection
        return True

    #Constraint to Culling Choose Selection not more than 1
    @api.one
    @api.constrains('cullinglineall_ids')
    def _constrains_choose_selection(self):
        if self.cullinglineall_ids:
            temp={}
            for selection in self.cullinglineall_ids:
                selection_value_name = selection.selection_id.name
                stage_selection_name = selection.selectionstage_id.name
                if selection_value_name in temp.values():
                    error_msg = "Selection Abnormal Selection Seed \"%s\" is set more than once " % stage_selection_name
                    raise exceptions.ValidationError(error_msg)
                temp[selection.id] = selection_value_name
            return temp

    #Constraint to Culling Choose Batch not more than 1
    @api.one
    @api.constrains('cullingline_ids')
    def _constrains_choose_batch(self):
        if self.cullingline_ids:
            temp={}
            for batch in self.cullingline_ids:
                batch_value_name = batch.batch_id.name
                if batch_value_name in temp.values():
                    error_msg = "Selection Abnormal Batch Seed \"%s\" is set more than once " % batch_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[batch.id] = batch_value_name
            return temp

    #state for Culling
    @api.one
    def action_draft(self):
        """Set Culling State to Draft."""
        self.state = 'draft'

    @api.one
    def action_confirmed(self):
        """Set Culling state to Confirmed."""
        self.state = 'confirmed'

    @api.one
    def action_approved1(self):
        """Set Culling state to Confirmed."""
        self.state = 'approved1'

    @api.one
    def action_approved2(self):
        """Set Culling state to Confirmed."""
        self.state = 'approved2'

    @api.one
    def action_approved3(self):
        """Set Culling state to Confirmed."""
        self.state = 'approved3'

    @api.one
    def action_approved(self):
        """Approved Culling Seed."""
        serial = self.env['estate.nursery.culling'].search_count([]) + 1
        self.write({'name':"Culling Seed  %d" %serial})
        self.action_receive()
        self.state = 'done'

    @api.one
    def action_receive(self):
        abnormal = self.total_quantityabnormal_temp
        abnormalbatch = self.quantitytotal_abnormal
        cullinglineids = self.cullinglineall_ids
        batchlineids = self.cullingline_ids
        serial = self.env['estate.nursery.request'].search_count([]) + 1
        if self.selectionform == '1':
            for itembatch in batchlineids:
                abnormalbatch += itembatch.total_qty_abnormal_batch
            self.write({'quantitytotal_abnormal': self.quantitytotal_abnormal,
                        'name': "Culling Seed  %d" % serial })
            self.action_move()

        elif self.selectionform == '2':
            for item in cullinglineids:
                abnormal += item.qty_abnormal_selection
            self.write({'total_quantityabnormal_temp': self.total_quantityabnormal_temp,
                        'name': "Culling Seed  %d" % serial })
            self.action_move()
        return True

    # Move quantity from culling location to inventory loss
    @api.one
    def action_move(self):
        if self.selectionform == '1' :
             location_ids = set()
             batch_ids = set()
             for itembatch in self.cullingline_ids:
                 if itembatch.culling_location_id and itembatch.batch_id and itembatch.total_qty_abnormal_batch > 0:
                     # location_ids.add(itembatch.culling_location_id)
                     batch_ids.add(itembatch.batch_id.culling_location_id.inherit_location_id)

                 for locationbatch in batch_ids:

                    qty_total_cullingbatch = 0

                    trash = self.env['estate.nursery.cullinglinebatch'].search([('batch_id', '=', locationbatch.id),
                                                                        ('culling_id', '=', self.id),
                                                                        ('culling_location_id','=',locationbatch.id)])
                    for i in trash:
                        qty_total_cullingbatch = i.total_qty_abnormal_batch

                 move_data = {
                        'product_id': itembatch.product_id.id,
                        'product_uom_qty': qty_total_cullingbatch,
                        'origin':self.culling_code,
                        'product_uom': itembatch.product_id.uom_id.id,
                        'name': 'Culling Abnormal Kecambah for %s:'%(self.culling_code),
                        'date_expected': self.culling_date,
                        'location_id': itembatch.culling_location_id.inherit_location_id.id,
                        'location_dest_id': self.location_type.id,
                        'state': 'confirmed', # set to done if no approval required
                        'restrict_lot_id': itembatch.lot_id.id # required by check tracking product
                 }
                 move = self.env['stock.move'].create(move_data)
                 move.action_confirm()
                 move.action_done()
             return True

        elif self.selectionform == '2':
             location_ids = set()
             selection_ids= set()
             for item in self.cullinglineall_ids:
                 if  item.batch_id and item.culling_location_id and item.total_abnormal > 0:
                     location_ids.add(item.culling_location_id.inherit_location_id)
                     selection_ids.add(item.selection_id)

                 for batchitem in selection_ids:
                     qty_batch = 0
                     batch = self.env['estate.nursery.cullingline'].search([('selection_id','=',batchitem.id),
                                                                        ('culling_id','=',self.id)])

                     for b in batch:
                         qty_batch = b.qty_abnormal_selection

                 move_data = {
                        'product_id': item.batch_id.product_id.id,
                        'product_uom_qty': item.qty_abnormal_selection,
                        'product_uom': batchitem.batch_id.product_id.uom_id.id,
                        'origin':self.culling_code,
                        'name': 'Culling Abnormal Bibit for %s:'%(self.culling_code),
                        'date_expected': self.culling_date,
                        'location_id': item.culling_location_id.inherit_location_id.id,
                        'location_dest_id': self.location_type.id,
                        'state': 'confirmed', # set to done if no approval required
                        'restrict_lot_id': item.lot_id.id # required by check tracking product
                        }
                 move = self.env['stock.move'].create(move_data)
                 move.action_confirm()
                 move.action_done()
             return True



class CullingLine(models.Model):

    _name="estate.nursery.cullingline"

    name=fields.Char(related='culling_id.name')
    culling_id=fields.Many2one('estate.nursery.culling')
    batch_id=fields.Many2one('estate.nursery.batch')
    selection_id=fields.Many2one('estate.nursery.selection')
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)],related='selection_id.batch_id.lot_id')
    product_id = fields.Many2one('product.product', "Product",)
    selectionstage_id=fields.Many2one('estate.nursery.selectionstage',
                                      related='selection_id.selectionstage_id',readonly=True)
    allqty_normal_batch=fields.Integer('Quantity All Normal Batch',compute='_get_total_allnormal_dobatch')
    allqty_abnormal_batch=fields.Integer()
    allqty_transplanted=fields.Integer()
    qty_normal_selection=fields.Integer('Quantity Normal Selection',compute='_get_qty_abnormalselection')
    qty_abnormal_selection=fields.Integer(related='selection_id.qty_abnormal')
    total_transplanted=fields.Integer('Quantity Total Transplanted',compute='_get_total_allplanted')
    total_abnormal=fields.Integer(store=True,compute='_get_total_abnormal')
    total_seed_dobatch=fields.Integer('Total Seed Do Batch',compute='_get_total_seed_dobatch')
    picking_id = fields.Many2one('stock.picking', "Picking", readonly=True ,)
    culling_location_id = fields.Many2one('estate.block.template',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),('scrap_location', '=', True)]
                                          ,store=True,related='selection_id.culling_location_id',readonly=True)

    @api.multi
    @api.onchange('batch_id')
    def _onchange_batch_id(self):
        cullinglist = self.env['estate.nursery.cullingline'].search([])
        if self:
            arrCullinglist = []
            for batch in cullinglist:
                arrCullinglist.append(batch.batch_id.id)
            return {
                'domain': {'batch_id': [('id','not in',arrCullinglist)]}
            }

    @api.multi
    @api.onchange('batch_id','selection_id')
    def _onchange_selection_id(self):
        arrBatch=[]
        if self:
            if self.batch_id:
                batchline = self.env['estate.nursery.selection'].search([('batch_id.id','=',self.batch_id[0].id)])
                for batch in batchline:
                    arrBatch.append(batch.batch_id.id)
                return {
                'domain': {'selection_id': [('batch_id.id','in',arrBatch)]}
            }

    # @api.multi
    # @api.onchange('selection_id')
    # def _onchange_selection_id(self):
    #     cullinglist = self.env['estate.nursery.cullingline'].search([])
    #     if self:
    #         arrCullinglist = []
    #         for a in cullinglist:
    #             arrCullinglist.append(a.selection_id.id)
    #         return {
    #             'domain': {'selection_id': [('id','not in',arrCullinglist),('qty_abnormal','>',0)]}
    #         }

    #get qty total do batch
    @api.one
    @api.onchange('selection_id','total_seed_dobatch')
    def _get_total_seed_dobatch(self):
        if self.selection_id:
                selection = self.env['estate.nursery.selection'].search([('id','=',self.selection_id.id)]).qty_batch
                self.total_seed_dobatch=selection

    #get qty normal batch
    @api.multi
    @api.onchange('selection_id','allqty_normal_batch')
    def _get_total_allnormal_dobatch(self):
        if self.selection_id:
            selection = self.env['estate.nursery.selection'].search([('id','=',self.selection_id.id),
                                                                      ('batch_id.id','=',self.batch_id.id)]).qty_normal
            self.allqty_normal_batch=selection

    #get qty normal Selection
    @api.multi
    @api.onchange('batch_id','selection_id','qty_normal_selection')
    def _get_qty_abnormalselection(self):
            if self.selection_id:
                selection = self.env['estate.nursery.selection'].search([('id','=',self.selection_id.id)]).qty_normal
                self.qty_normal_selection=selection

    #get qty abnormal batch
    @api.onchange('selection_id','allqty_abnormal_batch')
    def _get_total_allabnormal_dobatch(self):
        if self.selection_id:
            selection = self.env['estate.nursery.selection'].search([('id','=',self.selection_id.id),
                                                                      ('batch_id.id','=',self.batch_id.id)]).qty_abnormal
            self.allqty_abnormal_batch=selection

    #get qty Planted
    @api.multi
    @api.onchange('selection_id','total_transplanted')
    def _get_total_allplanted(self):
        if self.selection_id:
            selection = self.env['estate.nursery.selection'].search([('id','=',self.selection_id.id)]).qty_plant
            self.total_transplanted=selection

    @api.multi
    @api.onchange('product_id','selection_id')
    def _onchange_product_id(self):
        self.ensure_one()
        if self.selection_id:
            self.product_id = self.selection_id.batch_id.product_id

    #get  total qty abnormal
    @api.one
    @api.depends('qty_abnormal_selection','allqty_abnormal_batch','total_abnormal')
    def _get_total_abnormal(self):
        abnormalbatch=self.allqty_abnormal_batch
        abnormalselection=self.qty_abnormal_selection
        self.total_abnormal=abnormalselection+abnormalbatch


class CullinglineBatch(models.Model):

    _name = "estate.nursery.cullinglinebatch"

    def domain_batch(self):
        tempt=[]
        for record in self:
            tempt.append(record.batch_id)
        return tempt

    name=fields.Char("Culling line name",related='culling_id.name')
    culling_id=fields.Many2one('estate.nursery.culling')
    batch_id=fields.Many2one('estate.nursery.batch',)
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)],related='batch_id.lot_id')
    product_id = fields.Many2one('product.product', "Product",)
    qty_normal_batch=fields.Integer('Quantity Normal',compute='_get_qty_normal')
    qty_abnormal_batch=fields.Integer(related='batch_id.qty_abnormal')
    qty_transplanted=fields.Integer(store=True)
    total_qty_abnormal_batch=fields.Integer(store=True,compute='_get_abnormal_total')
    total_seed_do=fields.Integer(store=True)
    culling_location_id = fields.Many2one('estate.block.template',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),
                                                  ('scrap_location', '=', True)]
                                          ,store=True,related='batch_id.culling_location_id',readonly=True)

    #get qty Transplanted
    @api.multi
    @api.onchange('batch_id','qty_transplanted')
    def _get_qty_tranplanted(self):
        if self.batch_id:
         batch = self.env['estate.nursery.batch'].search([('id','=',self.batch_id.id)]).qty_planted_temp
         self.qty_transplanted=batch

    #get qty normal seed receive perbatch
    @api.multi
    @api.onchange('batch_id','qty_normal_batch')
    def _get_qty_normal(self):
        if self.batch_id:
            batch = self.env['estate.nursery.batch'].search([('id','=',self.batch_id.id)]).qty_normal
            self.qty_normal_batch=batch

    @api.multi
    @api.onchange('batch_id')
    def _onchange_batch_id(self):
        cullinglist = self.env['estate.nursery.cullinglinebatch'].search([])
        if self:
            arrCullinglist = []
            for a in cullinglist:
                arrCullinglist.append(a.batch_id.id)
            return {
                'domain': {'batch_id': [('id','not in',arrCullinglist),('qty_abnormal','>',0)]}
            }

    #get qty seed receive perbatch
    @api.multi
    @api.onchange('batch_id','total_seed_DO')
    def _get_qty_receive(self):
         if self.batch_id:
             batch = self.env['estate.nursery.batch'].search([('id','=',self.batch_id.id)]).qty_received
             self.total_seed_do=batch

    @api.multi
    @api.onchange('product_id','batch_id')
    def _onchange_product_id(self):
        self.ensure_one()
        if self.batch_id:
            self.product_id = self.batch_id.product_id

    #Total qty abnormal seed batch
    @api.one
    @api.depends('batch_id','total_qty_abnormal_batch')
    def _get_abnormal_total(self):
            total_abnormal = self.qty_abnormal_batch
            self.total_qty_abnormal_batch = total_abnormal








    