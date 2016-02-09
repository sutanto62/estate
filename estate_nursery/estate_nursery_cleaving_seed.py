from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
from openerp.exceptions import ValidationError
import calendar


class CleavingPolytone(models.Model):

    _name = "estate.nursery.cleaving"

    name=fields.Char("Cleaving polytone Code",related='batch_id.name')
    batch_id=fields.Many2one('estate.nursery.batch',"Batch")
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)],related='batch_id.lot_id')
    product_id = fields.Many2one('product.product', "Product", related="lot_id.product_id")
    cleaving_code=fields.Char()
    cleaving_date=fields.Date("Date of Cleaving polytone",required=True)
    cleavingline_ids=fields.One2many('estate.nursery.cleavingln','cleaving_id',"Cleaving line")
    stock_quant = fields.Many2one('stock.quant')
    qty_plantedbatch=fields.Integer(related='batch_id.qty_planted')
    qty_plante=fields.Integer()
    qty_singlebatch=fields.Integer()
    qty_doublebatch=fields.Integer()
    qty_abnormal=fields.Integer("Quantity Abnormal",compute="_compute_total_abnormal")
    qty_total=fields.Integer("Total All Seed ",compute="_compute_subtotal")
    qty_normal=fields.Integer("Quantity Normal",compute="_compute_total_normal")
    culling_location_id = fields.Many2one('stock.location',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),
                                                  ('scrap_location', '=', True)]
                                          ,store=True,required=True)
    location_type=fields.Many2one('stock.location',("location Last"),domain=[('name','=','Inventory loss'),
                                                                             ('usage','=','inventory'),
                                                                             ],store=True,required=True,
                                  default=lambda self: self.location_type.search([('name','=','Inventory loss')]))
    state=fields.Selection([('draft','Draft'),
        ('confirmed', 'Confirmed'),('approved1','First Approval'),('approved2','Second Approval'),
        ('done', 'Done')],string="Cleaving State")

    #Sequence cleaving code
    def create(self, cr, uid, vals, context=None):
        vals['cleaving_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.cleaving')
        res=super(CleavingPolytone, self).create(cr, uid, vals)
        return res

    # #get quantity Single
    @api.onchange('qty_singlebatch','batch_id')
    def _get_value_single(self):
       self.qty_singlebatch=self.batch_id.qty_single
       self.write({'qty_singlebatch':self.qty_singlebatch})

    #get quantity Double
    @api.onchange('qty_doublebatch','batch_id')
    def _get_value_double(self):
       self.qty_doublebatch=self.batch_id.qty_double
       self.write({'qty_doublebatch':self.qty_doublebatch})

    @api.one
    @api.depends('cleavingline_ids')
    def _compute_total_abnormal(self):
        self.qty_abnormal = 0
        if self.cleavingline_ids:
            for item in self.cleavingline_ids:
                self.qty_abnormal += item.qty_abnormal_double
        return True

    @api.one
    @api.depends('cleavingline_ids')
    def _compute_total_normal(self):
        self.qty_normal = 0
        if self.cleavingline_ids:
            for item in self.cleavingline_ids:
                self.qty_normal += item.qty_normal_double
        return True

    #compute Total Double after cleavage seed
    @api.one
    @api.depends('qty_normal','qty_plante','qty_doublebatch','qty_total','cleavingline_ids')
    def _compute_subtotal(self):
        normald = self.qty_normal
        double = self.qty_doublebatch
        if self.cleavingline_ids:
            total = (self.qty_plante-self.qty_doublebatch)+self.qty_normal
            self.qty_total=total
            print self.qty_total
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
    def action_approved(self):
        """Approved Selection is planted Seed."""
        self.action_receive()
        self.state = 'done'

    @api.one
    def action_receive(self):
        normal = self.qty_normal
        cleavagelineids = self.cleavingline_ids
        for itembatch in cleavagelineids:
            normal += itembatch.qty_normal_double
        self.write({'qty_normal': self.qty_normal })
        self.action_move()

    @api.one
    def action_move(self):
        location_ids = set()
        for item in self.cleavingline_ids:
            if item.location_id and item.qty_double > 0: # todo do not include empty quantity location
                location_ids.add(item.location_id)

        for location in location_ids:
            qty_total_double = 0
            qty = self.env['estate.nursery.cleavingln'].search([('location_id', '=', location.id),
                                                                   ('cleaving_id', '=', self.id)
                                                                   ])
            for i in qty:
                qty_total_double += i.qty_double

            move_data = {
                'product_id': self.batch_id.product_id.id,
                'product_uom_qty': qty_total_double,
                'product_uom': self.batch_id.product_id.uom_id.id,
                'name': 'Selection Abnormal.%s: %s'%(self.cleaving_code,self.batch_id.name),
                'date_expected': self.cleaving_date,
                'location_id': location.id,
                'location_dest_id':self.location_type.id,
                'state': 'confirmed', # set to done if no approval required
                'restrict_lot_id': self.lot_id.id # required by check tracking product
            }
            move = self.env['stock.move'].create(move_data)
            move.action_confirm()
            move.action_done()


        batch_ids = set()
        for itembatch in self.cleavingline_ids:
            if  itembatch.location_id and itembatch.qty_normal_double > 0:
                batch_ids.add(itembatch.location_id)

            for batchpisah in batch_ids:

                qty_total_cullingbatch = 0

                trash = self.env['estate.nursery.cleavingln'].search([('location_id', '=', batchpisah.id),
                                                                        ('cleaving_id', '=', self.id)])
                for i in trash:
                    qty_total_cleavagebatch = i.qty_normal_double

            move_data = {
                        'product_id': self.batch_id.product_id.id,
                        'product_uom_qty': qty_total_cleavagebatch,
                        'product_uom': self.batch_id.product_id.uom_id.id,
                        'name': 'Cleveage Normal Kecambah  %s for %s:'%(self.cleaving_code,self.batch_id.name),
                        'date_expected': self.cleaving_date,
                        'location_id': itembatch.location_type.id,
                        'location_dest_id': itembatch.location_id.id,
                        'state': 'confirmed', # set to done if no approval required
                        'restrict_lot_id': self.lot_id.id # required by check tracking product
                 }
            move = self.env['stock.move'].create(move_data)
            move.action_confirm()
            move.action_done()

            if  itembatch.location_id and itembatch.qty_abnormal_double > 0:
                batch_ids.add(itembatch.location_id)

            for batchpisah in batch_ids:

                qty_total_cullingbatch = 0

                trash = self.env['estate.nursery.cleavingln'].search([('location_id', '=', batchpisah.id),
                                                                        ('cleaving_id', '=', self.id)])
                for i in trash:
                    qty_total_cleavagebatch = i.qty_abnormal_double

            move_data = {
                        'product_id': self.batch_id.product_id.id,
                        'product_uom_qty': itembatch.qty_abnormal_double,
                        'product_uom': self.batch_id.product_id.uom_id.id,
                        'name': 'Cleaving Abnormal Kecambah  %s for %s:'%(self.cleaving_code,self.batch_id.name),
                        'date_expected': self.cleaving_date,
                        'location_id': itembatch.location_type.id,
                        'location_dest_id': self.culling_location_id.id,
                        'state': 'confirmed', # set to done if no approval required
                        'restrict_lot_id': self.lot_id.id # required by check tracking product
                 }
            move = self.env['stock.move'].create(move_data)
            move.action_confirm()
            move.action_done()
        return True



class CleavingLine(models.Model):

    _name="estate.nursery.cleavingln"

    name=fields.Char(related='cleaving_id.name')
    cleaving_id=fields.Many2one('estate.nursery.cleaving')
    batch_id=fields.Many2one('estate.nursery.batch',)
    location_id=fields.Many2one('stock.location', "Bedengan/Plot",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '3'),
                                          ('estate_location_type', '=', 'nursery'),
                                          ('scrap_location', '=', False)],
                                  help="Fill in location seed planted.",required=True)
    location_type=fields.Many2one('stock.location',("location Last"),domain=[('name','=','Virtual Separation'),
                                                                             ('usage','=','inventory'),
                                                                             ],store=True,required=True,
                                  default=lambda self: self.location_type.search([('name','=','Virtual Separation')]))
    qty_planted=fields.Integer(required=True)
    qty_single=fields.Integer(required=True)
    qty_double=fields.Integer(required=True)
    qty_normal_double=fields.Integer("Normal Double Seed",store=True,required=True)
    qty_abnormal_double=fields.Integer("Abnormal Double Seed",store=True,compute='_compute_abnormal')
    # total_lastsaldo=fields.Integer(readonly=True,compute="_compute_subtotal",store=True)


    # get quantity Planted
    @api.onchange('qty_planted','cleaving_id')
    def _get_value_planted(self):
       self.qty_planted=self.cleaving_id.qty_plante

    # get quantity Single
    @api.onchange('qty_single','cleaving_id')
    def _get_value_single(self):
       self.qty_single=self.cleaving_id.qty_singlebatch
       self.write({'qty_single':self.qty_single})

    #get quantity Double
    @api.onchange('qty_double','cleaving_id')
    def _get_value_double(self):
       self.qty_double=self.cleaving_id.qty_doublebatch
       self.write({'qty_double':self.qty_double})

    #calculate normal double
    @api.multi
    @api.constrains('qty_double','qty_normal_double')
    def constraint_normal_double(self):
        double = self.qty_double
        max_double = int(double) * int(2)
        print max_double
        for obj in self :
            if  self.qty_normal_double > max_double:
                raise ValidationError("Your Qty normal more than Maximal Double: %s" % obj.qty_normal_double)

    #compute Total Abnormal Double
    @api.one
    @api.depends('qty_normal_double','qty_double')
    def _compute_abnormal(self):
        if self.qty_normal_double:
            maxdouble=int(self.qty_double)*int(2)
            totalabnormal= maxdouble-int(self.qty_normal_double)
            self.qty_abnormal_double=totalabnormal
        return True


