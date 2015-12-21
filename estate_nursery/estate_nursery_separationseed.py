from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar


class SeparationPolytone(models.Model):

    _name = "estate.nursery.separation"

    name=fields.Char("Separation polytone Code")
    batch_id=fields.Many2one("estate.nursery.batch")
    batchline_ids = fields.One2many('estate.nursery.batchline', 'separation_id', ("Seed Boxes"))
    separation_date=fields.Date("Date of separation polytone")
    date_received=fields.Date("Date received seed ", related='batch_id.date_received')
    variety_id=fields.Many2one("variety type ",)
    qtytotal_single=fields.Integer(compute='_compute_single')
    qtytotal_double=fields.Integer()
    qty_total=fields.Integer(related='batch_id.qty_normal')
    qty_lastsaldo=fields.Integer()
    comment=fields.Text("Add Comment And Description")

    @api.one
    @api.depends('batchline_ids',)
    def _compute_single(self):
        self.qty_single=0
        for item in self.batchline_ids:
            self.qtytotal_single += item.qty_single
    @api.one
    @api.depends('batchline_ids',)
    def _compute_double(self):
        self.qty_double=0
        for item in self.batchline_ids:
            self.qtytotal_double += item.qty_double

class SeparationLine(models.Model):
    _name="estate.nursery.separationline"

    name=fields.Char()
    separation_id = fields.Many2one('estate.nursery.separation')
    location_id=fields.Many2one('stock.location', "Bedengan/Plot",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '3'),
                                          ('estate_location_type', '=', 'nursery'),
                                          ('scrap_location', '=', False)],
                                  help="Fill in location seed planted.")
    qty_single=fields.Integer()
    qty_double=fields.Integer()
    qty_normal=fields.Integer(related='separation_id.batch_id.qty_normal')


