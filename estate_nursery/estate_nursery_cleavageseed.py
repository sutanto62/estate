from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
from openerp.exceptions import ValidationError
import calendar


class PemisahanPolytone(models.Model):

    _name = "estate.nursery.cleavage"

    name=fields.Char("Separation polytone Code",related='batch_id.name')
    batch_id=fields.Many2one('estate.nursery.batch')
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)],related='batch_id.lot_id')
    product_id = fields.Many2one('product.product', "Product", related="lot_id.product_id")
    separation_code=fields.Char()
    separation_date=fields.Date("Date of separation polytone",required=True)
    cleavageline_ids=fields.One2many('estate.nursery.cleavageln','cleavage_id',"separation line")
    stock_quant = fields.Many2one('stock.quant')
    qty_plante=fields.Integer(readonly=True)
    qty_singlebatch=fields.Integer()
    qty_doublebatch=fields.Integer()
    qty_total=fields.Integer("Total All Seed ",compute="_compute_total_batch")
    culling_location_id = fields.Many2one('stock.location',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),('scrap_location', '=', True)]
                                          ,store=True,required=True)
    state=fields.Selection([('draft','Draft'),
        ('confirmed', 'Confirmed'),('approved1','First Approval'),('approved2','Second Approval'),
        ('done', 'Done')],string="Separation State")

    #Sequence separation code
    def create(self, cr, uid, vals, context=None):
        vals['separation_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.separation')
        res=super(PemisahanPolytone, self).create(cr, uid, vals)
        return res

    # #compute qtyplant :
    # @api.one
    # @api.depends('qty_total','qty_plant','qty_plante','cleavageline_ids')
    # def _compute_plannormal(self):
    #     plante = self.qty_plante
    #     if self.cleavageline_ids :
    #         plante = self.qty_total
    #         self.qty_plant=plante
    #     return  True

    #get quantity Single
    @api.onchange('qty_singlebatch','batch_id')
    def _get_value_single(self):
       self.qty_singlebatch=self.batch_id.qty_single
       self.write({'qty_singlebatch':self.qty_singlebatch})

    #get quantity Double
    @api.onchange('qty_doublebatch','batch_id')
    def _get_value_double(self):
       self.qty_doublebatch=self.batch_id.qty_double
       self.write({'qty_doublebatch':self.qty_doublebatch})

    #Calculate cleavage ids.
    @api.one
    @api.depends('cleavageline_ids')
    def _compute_total_batch(self):
        self.qty_total = 0
        if self.cleavageline_ids:
            for item in self.cleavageline_ids:
                self.qty_total += item.total_lastsaldo
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
        pemisahan = self.qty_total
        cleavagelineids = self.cleavageline_ids
        for itembatch in cleavagelineids:
            pemisahan += itembatch.total_lastsaldo
        self.write({'qty_total': self.qty_total })
        self.action_move()

    @api.one
    def action_move(self):
        batch_ids = set()
        for itembatch in self.cleavageline_ids:
            if  itembatch.location_id and itembatch.total_lastsaldo > 0:
                batch_ids.add(itembatch.location_id)

            for batchpisah in batch_ids:

                qty_total_cullingbatch = 0

                trash = self.env['estate.nursery.cleavageln'].search([('location_id', '=', batchpisah.id),
                                                                        ('cleavage_id', '=', self.id)])
                for i in trash:
                    qty_total_cleavagebatch = i.total_lastsaldo

            move_data = {
                        'product_id': self.batch_id.product_id.id,
                        'product_uom_qty': itembatch.total_lastsaldo,
                        'product_uom': self.batch_id.product_id.uom_id.id,
                        'name': 'Cleveage Normal Kecambah  %s for %s:'%(self.separation_code,self.batch_id.name),
                        'date_expected': self.separation_date,
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

                trash = self.env['estate.nursery.cleavageln'].search([('location_id', '=', batchpisah.id),
                                                                        ('cleavage_id', '=', self.id)])
                for i in trash:
                    qty_total_cleavagebatch = i.qty_abnormal_double

            move_data = {
                        'product_id': self.batch_id.product_id.id,
                        'product_uom_qty': itembatch.qty_abnormal_double,
                        'product_uom': self.batch_id.product_id.uom_id.id,
                        'name': 'Cleveage Abnormal Kecambah  %s for %s:'%(self.separation_code,self.batch_id.name),
                        'date_expected': self.separation_date,
                        'location_id': itembatch.location_type.id,
                        'location_dest_id': self.culling_location_id.id,
                        'state': 'confirmed', # set to done if no approval required
                        'restrict_lot_id': self.lot_id.id # required by check tracking product
                 }
            move = self.env['stock.move'].create(move_data)
            move.action_confirm()
            move.action_done()
        return True



class PemisahanLine(models.Model):

    _name="estate.nursery.cleavageln"

    name=fields.Char(related='cleavage_id.name')
    cleavage_id=fields.Many2one('estate.nursery.cleavage')
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
    qty_planted=fields.Integer()
    qty_single=fields.Integer()
    qty_double=fields.Integer()
    qty_normal_double=fields.Integer("Normal Double Seed",store=True,required=True)
    qty_abnormal_double=fields.Integer("Abnormal Double Seed",store=True,compute='_compute_abnormal')
    total_lastsaldo=fields.Integer(readonly=True,compute="_compute_subtotal",store=True)



    #get quantity Planted
    @api.onchange('qty_planted','cleavage_id')
    def _get_value_planted(self):
       self.qty_planted=self.cleavage_id.qty_plante
       self.write({'qty_planted':self.qty_planted})

    #get quantity Single
    @api.onchange('qty_single','cleavage_id')
    def _get_value_single(self):
       self.qty_single=self.cleavage_id.qty_singlebatch
       self.write({'qty_single':self.qty_single})

    #get quantity Double
    @api.onchange('qty_double','cleavage_id')
    def _get_value_double(self):
       self.qty_double=self.cleavage_id.qty_doublebatch
       self.write({'qty_double':self.qty_double})

    #calculate normal double
    @api.multi
    @api.constrains('qty_double','qty_normal_double')
    def constraint_normal_double(self):
        double = self.qty_double
        max_double = self.qty_double * int(2)
        for obj in self :
            if  self.qty_normal_double > max_double:
                raise ValidationError("Your Qty normal more than Maximal Double: %s" % obj.qty_normal_double)

    #compute Total Double after cleavage seed
    @api.one
    @api.depends('qty_normal_double','qty_planted','qty_double')
    def _compute_subtotal(self):
        normald = self.qty_normal_double
        double = self.qty_double
        total = (self.qty_planted-self.qty_double)+self.qty_normal_double
        self.total_lastsaldo=total

    #compute Total Abnormal Double
    @api.one
    @api.depends('qty_normal_double','qty_double')
    def _compute_abnormal(self):
        if self.qty_normal_double:
            maxdouble=self.qty_double*int(2)
            totalabnormal= maxdouble-int(self.qty_normal_double)
            self.qty_abnormal_double=totalabnormal
        return True


