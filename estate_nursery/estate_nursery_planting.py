from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar

class Planting(models.Model):
    #seed planting
    _name = "estate.nursery.planting"

class PlantingLine(models.Model):

    _name = "estate.nursery.plantingline"

class Requestplanting(models.Model):
    #request seed to plant
    _name = "estate.nursery.request"

    name=fields.Char("Request code",)
    bpb_code = fields.Char("BPB")
    batch_id=fields.Many2one('estate.nursery.batch',"Batch NO")
    requestline_ids=fields.One2many('estate.nursery.requestline','request_id',"RequestLine")
    partner_id=fields.Many2one('res.partner')
    picking_id=fields.Many2one('stock.picking', "Picking", readonly=True ,)
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)],related="batch_id.lot_id")
    product_id=fields.Many2one('product.product', "Product", related="lot_id.product_id")
    kebun_location_id = fields.Many2one('stock.location',"Estate Location",
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '1'),
                                                  ],
                                        default=lambda self: self.kebun_location_id.search
                                        ([('name','=','Liyodu Estate')]))
    date_request=fields.Date("Date Request",compute="_report_date")
    variety_id=fields.Many2one('estate.nursery.variety')
    total_qty_pokok = fields.Integer("Quantity Pokok Bibit")
    state=fields.Selection([('draft','Draft'),('reject','Rejected'),('cancel','Cancel'),
            ('pending','Pending'),('confirmed','Confirm'),
            ('validate1','First Approval'),('validate2','Second Approval')])

    #state
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
        """Approved Selection is planted Seed."""
        # self.action_receive()
        self.state = 'validate1'

    @api.one
    def action_approved2(self):
        """Approved Selection is planted Seed."""
        # self.action_receive()
        self.state = 'validate2'

    #sequence
    def create(self, cr, uid, vals, context=None):
        vals['bpb_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.request')
        res=super(Requestplanting, self).create(cr, uid, vals)
        return res

    #datetime

    @api.one
    @api.depends("date_request")
    def _report_date(self):
        today = datetime.now()
        self.date_request=today


class RequestLine(models.Model):
    _name = "estate.nursery.requestline"

    name=fields.Char("Requestline",related='request_id.name')
    request_id=fields.Many2one('estate.nursery.request')
    location_id = fields.Many2one('stock.location', "Bedengan/Plot",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '3'),
                                          ('estate_location_type', '=', 'nursery'),
                                          ('scrap_location', '=', False)],
                                  help="Fill in location seed planted.")
    Luas = fields.Float("Luas Block",digits=(2,2))
    qty_request = fields.Integer("Quantity Request")
    comment = fields.Text("Decription / Comment")


class TrasferSeed(models.Model):

    _name = "estate.nursery.trasfer"

