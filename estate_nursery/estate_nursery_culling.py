from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar


class Culling(models.Model):

    _name = "estate.nursery.culling"

    name=fields.Char("Culling Name",)
    culling_code=fields.Char("LBP")
    cullingline_ids=fields.One2many('estate.nursery.cullingline','culling_id',"Culling")
    culling_date = fields.Date("Culling date",store=True,required=True)
    batch_id=fields.Many2one('estate.nursery.batch')
    picking_id = fields.Many2one('stock.picking', "Picking", readonly=True )
    location_type=fields.Many2one('stock.location',("location Last"),domain=[('name','=','Inventory loss'),
                                                                             ('usage','=','inventory'),
                                                                             ],store=True,required=True)
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)],related='batch_id.lot_id')
    product_id = fields.Many2one('product.product', "Product", related="lot_id.product_id")
    stockquant_id=fields.Many2one('stock.quant',
                                  domain=[('location_id.estate_location_type', '=', 'nursery'),
                                          ('location_id.scrap_location','=',True),
                                          ('location_id.estate_location_level', '=', '3')],store=True)
    quantitytotal_abnormal = fields.Integer("Quantity Total Abnormal",compute='_compute_total',store=True)
    culling_location_id = fields.Many2one('stock.location',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),('scrap_location', '=', True)]
                                          ,store=True)
    state= fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),('approved1','First Approval '),('approved2','Second Approval'),
        ('done', 'Done')],string="Culling State")

    # #auto datetime
    # @api.one
    # @api.depends("culling_date")
    # def _culling_date(self):
    #     today = datetime.now()
    #     self.culling_date=today

    #Auto Generated Code of culling
    def create(self, cr, uid, vals, context=None):
        vals['culling_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.culling')
        res=super(Culling, self).create(cr, uid, vals)
        return res

    #calculate Culling Line
    @api.one
    @api.onchange('cullingline_ids','quantitytotal_abnormal')
    def _compute_total(self):
        self.quantitytotal_abnormal = 0
        for item in self.cullingline_ids:
            self.quantitytotal_abnormal += item.qty_abnormal
        return True

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
    def action_approved(self):
        """Approved Selection is planted Seed."""
        # self.action_receive()
        self.state = 'done'

    @api.one
    def action_receive(self):
        abnormal = self.quantitytotal_abnormal
        cullinglineids = self.cullingline_ids
        for item in cullinglineids:
            abnormal += item.qty_abnormal
        self.write({'quantitytotal_abnormal': self.quantitytotal_abnormal })
        # self.action_move()
        return True

    # @api.one
    # def action_move(self):
         # location_ids = set()
         # for item in self.cullingline_ids:
         #     if item.location_type and item.qty_abnormal > 0: # todo do not include empty quantity location
         #         location_ids.add(item.location_type)
         #
         # # Move quantity from culling location to inventory loss
         # for location in location_ids:
         #    qty_total_culling = 0
         #    trash = self.env['estate.nursery.cullingline'].search([('location_type', '=', location.id),
         #                                                            ('culling_id', '=', self.id)])
         #    for i in trash:
         #         qty_total_culling += i.qty_abnormal
         #
         #    move_data = {
         #            'product_id': self.stockquant_id.lot_id.product_id.id,
         #            'product_uom_qty': self.quantitytotal_abnormal,
         #            'product_uom': self.stockquant_id.lot_id.product_id.uom_id.id,
         #            'name': 'Cullling Abnormal for %s:'%(self.culling_code),
         #            'date_expected': self.culling_date,
         #            'location_id': self.stockquant_id.location_id.id,
         #            'location_dest_id': self.location_type.id,
         #            'state': 'confirmed', # set to done if no approval required
         #            'restrict_lot_id': self.lot_id.id # required by check tracking product
         #    }
         #
         #    move = self.env['stock.move'].create(move_data)
         #    move.action_confirm()
         #    move.action_done()
         # return True

         # if self.quantitytotal_abnormal > 0:
         #    move_data = {
         #        'product_id': self.stockquant_id.lot_id.product_id.id,
         #        'product_uom_qty': self.quantitytotal_abnormal,
         #        'product_uom': self.stockquant_id.lot_id.product_id.uom_id.id,
         #        'name': 'Cullling Abnormal.%s:'%(self.culling_code),
         #        'date_expected': self.culling_date,
         #        'location_id': self.stockquant_id.lot_id.id,
         #        'location_dest_id': self.location_type.id,
         #        'state': 'confirmed', # set to done if no approval required
         #        'restrict_lot_id': self.lot_id.id # required by check tracking product
         #    }
         #
         #    move = self.env['stock.move'].create(move_data)
         #    move.action_confirm()
         #    move.action_done()
         # return True


class Cullingline(models.Model):

    _name = "estate.nursery.cullingline"

    name=fields.Char("Culling line name",related='culling_id.name')
    culling_id=fields.Many2one('estate.nursery.culling')
    batch_id=fields.Many2one('estate.nursery.batch')
    selection_id=fields.Many2one('estate.nursery.selection',)
    qty_normal_batch=fields.Integer(readonly=True,store=True)
    qty_abnormal_batch=fields.Integer(readonly=True,store=True)
    qty_transplanted=fields.Integer(readonly=True,store=True)
    qty_abnormal_selection=fields.Integer(readonly=True,store=True)
    stockquant_id=fields.Many2one('stock.quant')
    total_seed_DO=fields.Integer(readonly=True,store=True)
    culling_location_id = fields.Many2one('stock.location',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),('scrap_location', '=', True)]
                                          ,store=True,related='batch_id.culling_location_id',readonly=True)
    qty_abnormal=fields.Integer('Quantity Total Abnormal',compute="_calculate_totalAbnormal",readonly=True,store=True)


    #get qty Transplanted
    @api.onchange('batch_id','qty_transplanted')
    def _get_qty_tranplanted(self):
        self.qty_transplanted=self.batch_id.qty_planted
        self.write({'qty_transplanted':self.qty_transplanted})
        print self.qty_transplanted

    #Calculate Total Abnormal
    @api.one
    @api.depends('batch_id','qty_abnormal_batch','qty_abnormal_selection')
    def _calculate_totalAbnormal(self):
            abnormalbatch=self.qty_abnormal_batch
            abnormalselection=self.qty_abnormal_selection
            self.qty_abnormal=abnormalbatch+abnormalselection
            print self.qty_abnormal

    #get qty normal seed receive perbatch
    @api.onchange('batch_id','qty_normal_batch')
    def _get_normal(self):
            self.qty_normal_batch=self.batch_id.qty_normal
            self.write({'qty_normal_batch':self.qty_normal_batch})
            print self.qty_normal_batch

    #get qty abnormal seed receive perbatch
    @api.onchange('batch_id','qty_abnormal_batch')
    def _get_abnormal(self):
            self.qty_abnormal_batch=self.batch_id.qty_abnormal
            self.write({'qty_abnormal_batch':self.qty_abnormal_batch})
            print self.qty_abnormal_batch

    #get qty seed receive perbatch
    @api.onchange('batch_id','total_seed_DO')
    def _get_receive(self):
            self.total_seed_DO=self.batch_id.qty_received
            self.write({'total_seed_DO':self.total_seed_DO})
            print self.total_seed_DO

    #get qty total selection perbatch
    @api.onchange('batch_id','qty_abnormal_selection','selection_id')
    def _getabnormal_selection(self):
            self.qty_abnormal_selection=self.batch_id.total_selection_abnormal
            self.write({'qty_abnormal_selection':self.qty_abnormal_selection})
            print self.qty_abnormal_selection


    # @api.depends('batch_id')
    # def getbatch(self):
    #     self.qty_abnormal_selection = 0
    #     for i in self.batch_id:
    #         self.qty_abnormal_selection = self.qty_abnormal_selection + self.batch_id.
    #     return theSum

    # @api.onchange('batch_id','qty_abnormal_selection','selection_ids')
    # def getValueAbnormal(self):
    #     if self.batch_id:
    #         self.qty_abnormal_selection=self.

    # #get value abnormal from batch
    # @api.one
    # @api.depends('selection_ids','batch_id')
    # def _compute_total(self):
    #     self.qty_planted = 0
    #     if self.batch_id:
    #         if self.selection_ids:
    #             for a in self.selection_ids:
    #                 self.qty_abnormal_selection +=a.qty_abnormal
    #                 print self.qty_abnormal_selection
    #
    #     return True
    #     # self.write({'qty_abnormal_selection' : self.qty_abnormal})

    #get abnormal from selection
    # @api.one
    # @api.depends('selection_id','batch_id','qty_abnormal_selection')
    # def _get_value_abnormal(self):
    #
    #     res={}
    #     batch=self.batch_id
    #     selection=self.selection_id
    #     if batch and selection:
    #         getselec=self.env('estate.nursery.selection').search(['qty_abnormal'])
    #         for r in self:
    #             r.qty_abnormal_selection = len(r.selectionline_ids)
    #             # for qtyplanted in self.batch_id:
        #     qty_planted = 0
        #     src = self.env['estate.nursery.batch'].search([('qty_planted', '=', True),
        #                                           ])
        #     src2 = self.env['estate.nursery.selection'].search([('qty_plant','=',True)])

    # @api.one
    # def search_qty_quant(self):
    #     location_stockids = set()
    #     for qty in self.stockquant_id:
    #         qty=0
    #         stock=self.env['stock.quant'].browse([('location_id.estate_location_type','=','nursery'),('qty','=',True)])
    #         print stock

    # related='stockquant_id.lot_id.qty',relation='stock.quant',store=True

# class StockQuant(models.Model):
#
#     _name="estate.nursery.stock"
#     _inherits = {'stock.quant':'stockquant_id'}
#
#     name=fields.Char("Quant name",compute="_get_name")
#     stockquant_id = fields.Many2one('stock.quant')
#     qty=fields.Integer(compute="_get_qty",select=True,readonly=True)
#     product_id= fields.Many2one('product.product', 'Product', required=True, ondelete="restrict", readonly=True, select=True),
#     location_id= fields.Many2one('stock.location', 'Location', required=True, ondelete="restrict", readonly=True, select=True, auto_join=True),
#     package_id= fields.Many2one('stock.quant.package', string='Package', help="The package containing this quant", readonly=True, select=True),
#
#
#     def _get_name(self, cr, uid, ids, name, args, context=None):
#         """ Forms complete name of location from parent location to child location.
#         @return: Dictionary of values
#         """
#         res = {}
#         for q in self.browse(cr, uid, ids, context=context):
#
#             res[q.id] = q.product_id.code or ''
#             if q.lot_id:
#                 res[q.id] = q.lot_id.name
#             res[q.id] += ': ' + q.product_id.uom_id.name
#         return res
#
#     def _get_qty(self,cr,uid,ids,qty,args,context=None):
#
#         res={}
#         for a in self.browse(cr,uid,ids,context=context):
#             res[a.id]= a.product_id.code or ''
#             if a.lot_id :
#                 res[a.id] = a.lot_id.name
#             res[a.id] += ":" + str(a.qty)
#         return res






    