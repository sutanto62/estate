from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar

class Planting(models.Model):
    #seed planting
    _name = "estate.nursery.seeddo"

    name=fields.Char("Planting Code")
    planting_code=fields.Char("Planting Code")
    request_ids=fields.One2many('estate.nursery.request','seeddoline_id','Request Line')
    seedline_ids=fields.One2many('estate.nursery.seedline','planting_id','Seed Request Line')
    product_id = fields.Many2one('product.product', "Product", related="lot_id.product_id")
    picking_id = fields.Many2one('stock.picking', "Picking", readonly=True)
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)])
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety", required=True, ondelete="restrict")
    seed_location_id = fields.Many2one('estate.block.template', ("Seed Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),
                                                  ('scrap_location', '=', False),
                                                  ])
    date_request = fields.Date('Date Seed Delivery Order')
    total_qty_pokok= fields.Date("Total Pokok")
    request_count=fields.Integer("Count Request Line", compute="_get_request_count")
    state=fields.Selection([('draft','Draft'),('confirmed','Confirm'),
            ('validate1','First Approval'),('validate2','Second Approval'),('done','Ordered')])

    #sequence
    def create(self, cr, uid, vals, context=None):
        vals['planting_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.seeddo')
        res=super(Planting, self).create(cr, uid, vals)
        return res

    #state
    @api.one
    def action_draft(self):
        """Set planting State to Draft."""
        self.state = 'draft'

    @api.one
    def action_confirmed(self):
        """Set Planting state to Confirmed."""
        self.state = 'confirmed'

    @api.one
    def action_approved1(self):
        """Approved planting is validate 1."""
        self.state = 'validate1'

    @api.one
    def action_approved2(self):
        """Approved Planting is validate 2."""
        self.state = 'validate2'

    @api.one
    def action_approved(self):
        """Approved Planting is done."""
        # self.action_receive()
        self.state = 'done'

    # @api.one
    # def action_receive(self):
    #     qty_req = self.total_qty_pokok
    #     requestlineids = self.requestline_ids
    #
    #     for item in requestlineids:
    #         qty_req += item.qty_request
    #     self.write({'total_qty_pokok': self.total_qty_pokok})
    #
    #     return True

    #count selection
    @api.one
    @api.depends('request_ids')
    def _get_request_count(self):
        for r in self:
            r.request_count = len(r.request_ids)


class SeedLine(models.Model):
    _name = "estate.nursery.seedline"

    name=fields.Char()
    request_id = fields.Many2one('estate.nursery.request')
    planting_id= fields.Many2one('estate.nursery.seeddo')
    qty_request=fields.Integer("Quantity Seed Transfer",related='request_id.total_qty_pokok')
    qty_transfer=fields.Integer("Quantity Seed Transfer")
    result_transfer=fields.Integer("Quantity Result")

    #calculate Result SPB
    @api.one
    @api.depends('qty_transfer','qty_result','qty_request')
    def calculate_qty_result(self):
        if self.qty_transfer:
            hasil = self.qty_request-self.qty_transfer
            self.qty_result= hasil
            print  self.qty_result
        return True

class Requestplanting(models.Model):
    #request seed to plant
    #delegation purchase order to BPB
    _name = "estate.nursery.request"

    # _inherits = {'purchase.order': 'purchase_id',}


    name=fields.Char("Request code")
    bpb_code = fields.Char("BPB")
    user_id=fields.Many2one('res.users')
    batch_id=fields.Many2one('estate.nursery.batch')
    requestline_ids=fields.One2many('estate.nursery.requestline','request_id',"RequestLine")
    partner_id=fields.Many2one('res.partner',required=True, ondelete="restrict",
                               default=lambda self: self.partner_id.search
                                        ([('name','=','Dami Mas Sejahtera')]))
    picking_id=fields.Many2one('stock.picking', "Picking", readonly=True ,)
    kebun_location_id = fields.Many2one('estate.block.template',"Estate Location",
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '1'),
                                                  ],
                                        default=lambda self: self.kebun_location_id.search
                                        ([('name','=','LYD')]))
    divisi_location_id = fields.Many2one('estate.block.template',"Divisi Location",
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '2'),
                                                  ],
                                        default=lambda self: self.divisi_location_id.search
                                        ([('name','=','Division 1')]))
    date_request=fields.Date("Date Request")
    variety_id=fields.Many2one('estate.nursery.variety',required=True,
                               default=lambda self: self.variety_id.search
                                        ([('name','=','Dura')]))
    comment=fields.Text("Cause Pending")
    total_qty_pokok = fields.Integer("Quantity Pokok Bibit",compute="_compute_total")
    state=fields.Selection([('draft','Draft'),('open2','Open Pending'),('pending2','Pending'),
            ('pending','Pending'),('confirmed','Confirm'),('open','Open Pending'),
            ('validate1','First Approval'),('validate2','Second Approval'),('done','Draft To SPB')])

    #state
    @api.one
    def action_draft(self):
        """Set planting State to Draft."""
        self.state = 'draft'
    @api.one
    def action_open_pending(self):
        """Set Planting State to open."""
        self.state = 'open'
    @api.one
    def action_open_pending2(self):
        """Set Planting State to open."""
        self.state = 'open2'
    @api.one
    def action_pending(self):
        """Set Selection State to pending."""
        self.state = 'pending'

    @api.one
    def action_pending2(self):
        """Set Selection State to pending."""
        self.state = 'pending2'

    @api.one
    def action_confirmed(self):
        """Set Planting state to Confirmed."""
        self.state = 'confirmed'

    @api.one
    def action_approved1(self):
        """Approved planting is validate 1."""
        self.state = 'validate1'

    @api.one
    def action_approved2(self):
        """Approved Planting is validate 2."""
        self.state = 'validate2'

    @api.one
    def action_approved(self):
        """Approved Planting is done."""
        self.action_receive()
        self.state = 'done'

    @api.one
    def action_receive(self):
        qty_req = self.total_qty_pokok
        requestlineids = self.requestline_ids

        for item in requestlineids:
            qty_req += item.qty_request
        self.write({'total_qty_pokok': self.total_qty_pokok})

        return True

    #compute RequestLine
    @api.one
    @api.depends('requestline_ids')
    def _compute_total(self):
        self.total_qty_pokok = 0
        if self.requestline_ids:
            for item in self.requestline_ids:
                self.total_qty_pokok += item.qty_request
        return True

    #sequence
    def create(self, cr, uid, vals, context=None):
        vals['bpb_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.request')
        res=super(Requestplanting, self).create(cr, uid, vals)
        return res

    # #datetime
    # @api.one
    # @api.depends("date_request")
    # def _report_date(self):
    #     today = datetime.now()
    #     self.date_request=today



class SeedDoLine(models.Model):
    _inherit = "estate.nursery.request"

    seeddoline_id= fields.Many2one("estate.nursery.seeddo")

class RequestLine(models.Model):
    _name = "estate.nursery.requestline"

    name=fields.Char("Requestline",related='request_id.name')
    request_id=fields.Many2one('estate.nursery.request')
    inherit_location_id = fields.Many2one('estate.block.template', "Block",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '2'),
                                          ('estate_location_type', '=', 'planted'),
                                          ('scrap_location', '=', False)],
                                  help="Fill in location seed planted.",)
    Luas = fields.Float("Luas Block",digits=(2,2),related='inherit_location_id.area_planted',readonly=True)
    qty_request = fields.Integer("Quantity Request",required=True)
    comment = fields.Text("Decription / Comment")


class TrasferSeed(models.Model):

    _name = "estate.nursery.trasfer"

