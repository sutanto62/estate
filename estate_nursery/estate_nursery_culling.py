from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
from openerp.exceptions import ValidationError
import calendar


class Culling(models.Model):

    _name = "estate.nursery.culling"

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
    selectionform=fields.Selection([('0','None'),('1','Batch'),('2','Selection')],default='1',required=True)
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

    #state for Culling
    @api.one
    def action_draft(self):
        """Set Selection State to Draft."""
        self.state = 'draft'

    @api.one
    def action_confirmed(self):
        """Set Selection state to Confirmed."""
        self.state = 'confirmed'

    @api.one
    def action_approved1(self):
        """Set Selection state to Confirmed."""
        self.state = 'approved1'

    @api.one
    def action_approved2(self):
        """Set Selection state to Confirmed."""
        self.state = 'approved2'

    @api.one
    def action_approved3(self):
        """Set Selection state to Confirmed."""
        self.state = 'approved3'

    @api.one
    def action_approved(self):
        """Approved Selection is planted Seed."""
        self.action_receive()
        self.state = 'done'

    @api.one
    def action_receive(self):
        abnormal = self.total_quantityabnormal_temp
        abnormalbatch = self.quantitytotal_abnormal
        cullinglineids = self.cullinglineall_ids
        batchlineids = self.cullingline_ids

        if self.selectionform == '1':
            for itembatch in batchlineids:
                abnormalbatch += itembatch.total_qty_abnormal_batch
            self.write({'quantitytotal_abnormal': self.quantitytotal_abnormal })
            self.action_move()

        elif self.selectionform == '2':
            for item in cullinglineids:
                abnormal += item.qty_abnormal_selection
            self.write({'total_quantityabnormal_temp': self.total_quantityabnormal_temp })
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
                        'product_uom_qty': itembatch.total_qty_abnormal_batch,
                        'product_uom': itembatch.product_id.uom_id.id,
                        'name': 'Culling Abnormal Kecambah for %s:'%(self.culling_code),
                        'date_expected': self.culling_date,
                        'location_id': itembatch.culling_location_id.id,
                        'location_dest_id': self.location_type.id,
                        'state': 'confirmed', # set to done if no approval required
                        'restrict_lot_id': itembatch.lot_id.id # required by check tracking product
                 }
                 print(move_data)
                 move = self.env['stock.move'].create(move_data)
                 move.action_confirm()
                 move.action_done()
             return True

        elif self.selectionform == '2':
             location_ids = set()
             selection_ids= set()
             for item in self.cullinglineall_ids:
                 if  item.batch_id and item.culling_location_id and item.total_abnormal > 0:
                     location_ids.add(item.culling_location_id)
                     selection_ids.add(item.selection_id)

                 for batchitem in selection_ids:
                     qty_batch = 0
                     batch = self.env['estate.nursery.cullingline'].search([('selection_id','=',batchitem.id),
                                                                        ('culling_id','=',self.id)])

                     for b in batch:
                         qty_batch = b.qty_abnormal_selection

                 move_data = {
                        'product_id': item.product_id.id,
                        'product_uom_qty': item.qty_abnormal_selection,
                        'product_uom': item.product_id.uom_id.id,
                        'name': 'Culling Abnormal Bibit for %s:'%(self.culling_code),
                        'date_expected': self.culling_date,
                        'location_id': item.culling_location_id.id,
                        'location_dest_id': self.location_type.id,
                        'state': 'confirmed', # set to done if no approval required
                        'restrict_lot_id': item.lot_id.id # required by check tracking product
                        }
                 print(move_data)
                 move = self.env['stock.move'].create(move_data)
                 move.action_confirm()
                 move.action_done()
             return True


class CullingLine(models.Model):

    _name="estate.nursery.cullingline"



    name=fields.Char(related='culling_id.name')
    culling_id=fields.Many2one('estate.nursery.culling')
    batch_id=fields.Many2one('estate.nursery.batch')
    selection_id=fields.Many2one('estate.nursery.selection',domain="[('qty_abnormal','>',0)]"
                                 )
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)],related='selection_id.batch_id.lot_id')
    product_id = fields.Many2one('product.product', "Product", related="selection_id.lot_id.product_id")
    selectionstage_id=fields.Many2one('estate.nursery.selectionstage',
                                      related='selection_id.selectionstage_id',readonly=True)
    testflag=fields.Selection(related='selection_id.flagcul')
    status=fields.Boolean()
    allqty_normal_batch=fields.Integer()
    allqty_abnormal_batch=fields.Integer()
    allqty_transplanted=fields.Integer()
    qty_normal_selection=fields.Integer()
    qty_abnormal_selection=fields.Integer(related='selection_id.qty_abnormal')
    total_transplanted=fields.Integer()
    total_abnormal=fields.Integer(store=True,compute='_get_total_abnormal')
    total_seed_dobatch=fields.Integer()
    picking_id = fields.Many2one('stock.picking', "Picking", readonly=True ,)
    culling_location_id = fields.Many2one('estate.block.template',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),('scrap_location', '=', True)]
                                          ,store=True,related='selection_id.culling_location_id',readonly=True)

    #Validation to set flag in selection id
    @api.one
    @api.onchange('selection_id','testflag')
    def test(self):
        flag = self.selection_id.flagcul
        state = self.culling_id.state
        if self.culling_id:
            if self.culling_id.state == 'confirmed':
                self.status = True


        # if self.selection_id :
        #         flag='2'
        #         self.write({'flagcul' : flag})
        #         if  flag== '1':
        #             self.status = True
        #         elif flag== '2':
        #             self.status = True
        # return {'value': {'flagcul':flag}}

        # elif self.selection_id == True and state == 'confirmed':
        #         flag='1'
        #         self.write({'flagcul' : flag})
        #         if  flag== '1':
        #             self.status = True
        # print flag
    # @api.onchange('selection_id','culling_id')
    # def change_flag(self):
    #     flag = self.selection_id.flagcul
    #     print flag
    #     if self.selection_id==True:
    #         flag = '1'
    #         self.write({'flagcul' : flag})
    #         print flag






    #get qty total do batch
    @api.onchange('selection_id','total_seed_dobatch')
    def _get_total_seed_dobatch(self):
        self.total_seed_dobatch=self.selection_id.qty_batch
        self.write({'total_seed_dobatch':self.total_seed_dobatch})
        print self.total_seed_dobatch

    #get qty normal batch
    @api.onchange('selection_id','allqty_normal_batch')
    def _get_total_allnormal_dobatch(self):
        self.allqty_normal_batch=self.selection_id.qty_nor_batch
        self.write({'allqty_normal_batch':self.allqty_normal_batch})
        print self.allqty_normal_batch

    #get qty normal Selection
    @api.onchange('batch_id','selection_id','qty_normal_selection')
    def _get_qty_abnormalselection(self):
            self.qty_normal_selection=self.selection_id.qty_normal
            self.write({'qty_normal_selection':self.qty_normal_selection})
            print self.qty_normal_selection

    #get qty abnormal batch
    @api.onchange('selection_id','allqty_abnormal_batch')
    def _get_total_allabnormal_dobatch(self):
        self.allqty_abnormal_batch=self.selection_id.qty_abn_batch
        self.write({'allqty_abnormal_batch':self.allqty_abnormal_batch})
        print self.allqty_abnormal_batch

    #get qty Planted
    @api.onchange('selection_id','total_transplanted')
    def _get_total_allplanted(self):
        self.total_transplanted=self.selection_id.qty_tpr_batch
        self.write({'total_transplanted':self.total_transplanted})
        print self.total_transplanted

    #get  total qty abnormal
    @api.one
    @api.depends('qty_abnormal_selection','allqty_abnormal_batch','total_abnormal')
    def _get_total_abnormal(self):
        abnormalbatch=self.allqty_abnormal_batch
        abnormalselection=self.qty_abnormal_selection
        self.total_abnormal=abnormalselection+abnormalbatch
        print self.total_abnormal

class CullinglineBatch(models.Model):

    _name = "estate.nursery.cullinglinebatch"

    name=fields.Char("Culling line name",related='culling_id.name')
    culling_id=fields.Many2one('estate.nursery.culling')
    batch_id=fields.Many2one('estate.nursery.batch',domain="[('qty_abnormal','>',0)]")
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)],related='batch_id.lot_id')
    product_id = fields.Many2one('product.product', "Product", related="lot_id.product_id")
    qty_normal_batch=fields.Integer()
    qty_abnormal_batch=fields.Integer(related='batch_id.qty_abnormal')
    qty_transplanted=fields.Integer(store=True)
    total_qty_abnormal_batch=fields.Integer(store=True,compute='_get_abnormal_total')
    total_seed_DO=fields.Integer(store=True)
    culling_location_id = fields.Many2one('estate.block.template',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),
                                                  ('scrap_location', '=', True)]
                                          ,store=True,related='batch_id.culling_location_id',readonly=True)

    #get qty Transplanted
    @api.onchange('batch_id','qty_transplanted')
    def _get_qty_tranplanted(self):
        self.qty_transplanted=self.batch_id.qty_planted_temp
        self.write({'qty_transplanted':self.qty_transplanted})
        print self.qty_transplanted

    #get qty normal seed receive perbatch
    @api.onchange('batch_id','qty_normal_batch')
    def _get_normal(self):
            self.qty_normal_batch=self.batch_id.qty_normal
            self.write({'qty_normal_batch':self.qty_normal_batch})
            print self.qty_normal_batch

    #get qty seed receive perbatch
    @api.onchange('batch_id','total_seed_DO')
    def _get_receive(self):
            self.total_seed_DO=self.batch_id.qty_received
            self.write({'total_seed_DO':self.total_seed_DO})
            print self.total_seed_DO

    #Total qty abnormal seed batch
    @api.one
    @api.depends('batch_id','total_qty_abnormal_batch')
    def _get_abnormal_total(self):
            total_abnormal = self.qty_abnormal_batch
            self.total_qty_abnormal_batch = total_abnormal
            print  self.total_qty_abnormal_batch






    