from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar


class PemisahanPolytone(models.Model):

    _name = "estate.nursery.separation"

    name=fields.Char("Separation polytone Code")
    separation_code=fields.Char()
    separation_date=fields.Date("Date of separation polytone")
    separationline_ids=fields.One2many('estate.nursery.separationln','separation_id',"Separation Line")
    qty_total=fields.Integer("Total Seed ")
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



class PemisahanLine(models.Model):

    _name="estate.nursery.separationln"

    name=fields.Char(related='separation_id.name')
    separation_id=fields.Many2one('estate.nursery.separation')
    # batch_id=fields.Many2one('estate.nursery.batch')
    # location_id=fields.Many2one('stock.location', "Bedengan/Plot",
    #                               domain=[('estate_location', '=', True),
    #                                       ('estate_location_level', '=', '3'),
    #                                       ('estate_location_type', '=', 'nursery'),
    #                                       ('scrap_location', '=', False)],
    #                               help="Fill in location seed planted.")
    qty_planted=fields.Integer()
    qty_single=fields.Integer()
    qty_double=fields.Integer()
    qty_normal_double=fields.Integer("Normal Double Seed",store=True)
    qty_abnormal_double=fields.Integer("Abnormal Double Seed",store=True)
    total_lastsaldo=fields.Integer()



