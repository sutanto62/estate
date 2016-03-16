from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar


class Requestplanting(models.Model):
    #request seed to plant
    #delegation purchase order to BPB
    _name = "estate.nursery.request"
    _description = "Request Purchase Seed"
    _inherit = ['mail.thread']

    # _inherits = {'purchase.order': 'purchase_id',}


    name=fields.Char("Request code")
    bpb_code = fields.Char("BPB")
    user_id=fields.Many2one('res.users')
    batch_id=fields.Many2one('estate.nursery.batch')
    requestline_ids=fields.One2many('estate.nursery.requestline','request_id',"RequestLine")
    partner_id=fields.Many2one('res.partner',required=True, ondelete="restrict",
                               default=lambda self: self.partner_id.search
                                        ([('name','=','Dami Mas Sejahtera')]),track_visibility='onchange')
    picking_id=fields.Many2one('stock.picking', "Picking", readonly=True ,)
    kebun_location_id = fields.Many2one('estate.block.template',"Estate Location",track_visibility='onchange',
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '1'),
                                                  ],
                                        default=lambda self: self.kebun_location_id.search
                                        ([('name','=','LYD')]))
    divisi_location_id = fields.Many2one('estate.block.template',"Divisi Location",track_visibility='onchange',
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '2'),
                                                  ],
                                        default=lambda self: self.divisi_location_id.search
                                        ([('name','=','Division 1')]))
    date_request=fields.Date("Date Request",track_visibility='onchange')
    variety_id=fields.Many2one('estate.nursery.variety',required=True,track_visibility='onchange',
                               default=lambda self: self.variety_id.search
                                        ([('name','=','Dura')]))
    comment=fields.Text("Cause Pending")
    total_qty_pokok = fields.Integer("Quantity Pokok Bibit",compute="_compute_total",track_visibility='onchange')
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
        serial = self.env['estate.nursery.request'].search_count([]) + 1

        for item in requestlineids:
            qty_req += item.qty_request
        self.write({'total_qty_pokok': self.total_qty_pokok,'name': "Request Seed  %d" % serial,})
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

    #constraint for location division select more than one in 1 spb
    @api.one
    @api.constrains('requestline_ids')
    def _constrains_requestline(self):
        if self.requestline_ids:
            temp={}
            for division in self.requestline_ids:
                division_value_name = division.inherit_location_id.name
                if division_value_name in temp.values():
                    error_msg = "Division for Block \"%s\" is set more than once " % division_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[division.id] = division_value_name
            return temp

class RequestLine(models.Model):

    _name = "estate.nursery.requestline"

    name=fields.Char("Requestline",related='request_id.name')
    request_id=fields.Many2one('estate.nursery.request',ondelete='cascade')
    inherit_location_id = fields.Many2one('estate.block.template', ("Seed Location"),track_visibility='onchange',
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'planted'),
                                                  ('scrap_location', '=', False),
                                                  ])
    Luas = fields.Float("Luas Block",digits=(2,2),related='inherit_location_id.area_planted',readonly=True)
    qty_request = fields.Integer("Quantity Request",required=True)
    comment = fields.Text("Decription / Comment")


    #constraint qty Request not moree than standard qty sph
    @api.one
    @api.constrains('qty_request','inherit_location_id')
    def check_qty_request(self):
        qty_standard = self.inherit_location_id.qty_sph_standard
        qty_do = self.inherit_location_id.qty_sph_do
        if self.qty_request:
            if self.inherit_location_id.qty_sph_standard:
                if self.qty_request > qty_standard:
                    error_msg = "Selection Stage Seed \"%s\" quantity is set not more than 126 " % self.inherit_location_id.name
                    raise exceptions.ValidationError(error_msg)
            elif self.inherit_location_id.qty_sph_do:
                if self.qty_request > qty_do:
                    error_msg = "Selection Stage Seed \"%s\" quantity is set not more than 130 " % self.inherit_location_id.name
                    raise exceptions.ValidationError(error_msg)
            return True

    #onchange
    # @api.one
    # @api.onechange('qty_request','inherit_location_id')
    # def onchange_qty_request(self):
    #     if self.inherit_location_id:
    #         self.qty_request = 0
    #         self.qty_request += self.inherit_location_id.