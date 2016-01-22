from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
from openerp.exceptions import ValidationError
import calendar


class PemisahanPolytone(models.Model):

    _name = "estate.nursery.cleavage"

    name=fields.Char("Separation polytone Code")
    separation_code=fields.Char()
    separation_date=fields.Date("Date of separation polytone")
    cleavageline_ids=fields.One2many('estate.nursery.cleavageln','cleavage_id',"separation line")
    qty_total=fields.Integer("Total All Seed ",compute="_compute_total_batch")
    culling_location_id = fields.Many2one('stock.location',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),('scrap_location', '=', True)]
                                          ,store=True)
    state=fields.Selection([('draft','Draft'),
        ('confirmed', 'Confirmed'),('approved1','First Approval'),('approved2','Second Approval'),
        ('done', 'Done')],string="Separation State")

    #Sequence separation code
    def create(self, cr, uid, vals, context=None):
        vals['separation_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.separation')
        res=super(PemisahanPolytone, self).create(cr, uid, vals)
        return res

    #Calculate cleavage ids.
    @api.one
    @api.depends('cleavageline_ids')
    def _compute_total_batch(self):
        self.qty_total = 0
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
        # self.action_receive()
        self.state = 'done'

    # @api.one
    # def action_receive(self):
    #     abnormal = self.total_quantityabnormal_temp
    #     abnormalbatch = self.quantitytotal_abnormal
    #     cullinglineids = self.cullinglineall_ids
    #     batchlineids = self.cullingline_ids
    #     if self.selectionform == '1':
    #         for itembatch in batchlineids:
    #             abnormalbatch += itembatch.total_qty_abnormal_batch
    #         self.write({'quantitytotal_abnormal': self.quantitytotal_abnormal })
    #         self.action_move()
    #     elif self.selectionform == '2':
    #         for item in cullinglineids:
    #             abnormal += item.qty_abnormal_selection
    #         self.write({'total_quantityabnormal_temp': self.total_quantityabnormal_temp })
    #         self.action_move()
    #     return True

class PemisahanLine(models.Model):

    _name="estate.nursery.cleavageln"

    name=fields.Char(related='cleavage_id.name')
    cleavage_id=fields.Many2one('estate.nursery.cleavage')
    batch_id=fields.Many2one('estate.nursery.batch')
    location_id=fields.Many2one('stock.location', "Bedengan/Plot",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '3'),
                                          ('estate_location_type', '=', 'nursery'),
                                          ('scrap_location', '=', False)],
                                  help="Fill in location seed planted.",required=True)
    qty_planted=fields.Integer()
    qty_single=fields.Integer(related='batch_id.qty_single')
    qty_double=fields.Integer(related='batch_id.qty_double')
    qty_normal_double=fields.Integer("Normal Double Seed",store=True,required=True)
    qty_abnormal_double=fields.Integer("Abnormal Double Seed",store=True,compute='_compute_abnormal')
    total_lastsaldo=fields.Integer(readonly=True,compute="_compute_subtotal")


    #get quantity Planted
    @api.onchange('qty_planted','batch_id')
    def _get_value_planted(self):
       self.qty_planted=self.batch_id.qty_planted
       self.write({'qty_planted':self.qty_planted})
    #get quantity Single
    @api.onchange('qty_single','batch_id')
    def _get_value_single(self):
       self.qty_single=self.batch_id.qty_single
       self.write({'qty_single':self.qty_single})
    #get quantity Double
    @api.onchange('qty_double','batch_id')
    def _get_value_double(self):
       self.qty_double=self.batch_id.qty_double
       self.write({'qty_double':self.qty_double})
    #calculate normal double
    @api.constrains('qty_double','qty_normal_double')
    def constraint_normal_double(self):
        double = self.qty_double
        max_double = self.qty_double * int(2)
        for hit in self.qty_normal_double :
            if  hit.qty_normal_double > max_double:
                raise ValidationError("Your Qty normal more than Maximal Double: %s" % hit.qty_normal_double)
        return True
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


