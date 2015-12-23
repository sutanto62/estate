from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar


class Culling(models.Model):

    _name = "estate.nursery.culling"

    name=fields.Char("Culling Name",)
    culling_code=fields.Char("LBP")
    cullingline_ids=fields.One2many('estate.nursery.cullingline','culling_id',"Culling")
    culling_date = fields.Date("Culling date",)
    batch_id=fields.Many2one('estate.nursery.batch')
    quantitytotal_abnormal = fields.Integer("Quantity Total Abnormal")
    selection_type = fields.Selection([('1','Batch'),('2','Selection'),('3','ALL')])
    culling_location_id = fields.Many2one('stock.location',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),('scrap_location', '=', True)]
                                          ,related="batch_id.culling_location_id",store=True)
    state= fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')],string="Culling State")

    #sequence
    def create(self, cr, uid, vals, context=None):
        vals['culling_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.culling')
        res=super(Culling, self).create(cr, uid, vals)
        return res

    @api.one
    def action_draft(self):
        """Set Selection State to Draft."""
        self.state = 'draft'

    @api.one
    def action_confirmed(self):
        """Set Selection state to Confirmed."""
        self.state = 'confirmed'

    @api.one
    def action_approved(self):
        """Approved Selection is planted Seed."""
        # self.action_receive()
        self.state = 'done'

class Cullingline(models.Model):

    _name = "estate.nursery.cullingline"

    name=fields.Char("Culling line name",related='culling_id.name')
    culling_id=fields.Many2one('estate.nursery.culling')
    batch_id=fields.Many2one('estate.nursery.batch')
    selection_id=fields.Many2one('estate.nursery.selection',related='batch_id.selection_id')
    selectionstage_id=fields.Many2one('estate.nursery.selectionstage',related='selection_id.selectionstage_id',readonly=True)
    qty_abnormal_selection=fields.Integer(related='selection_id.qty_abnormal')
    qty_planted=fields.Integer(related='batch_id.qty_planted',readonly=True)
    qty_abnormal_batch=fields.Integer(related='batch_id.qty_abnormal',readonly=True)
    comment=fields.Text("Comment/Description")



    