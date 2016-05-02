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
    employee_id= fields.Many2one('hr.employee')
    batch_id=fields.Many2one('estate.nursery.batch')
    seeddo_id=fields.Many2one('estate.nursery.seeddo')
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
                                                  ('estate_location_type','=','planted')
                                                  ],
                                        default=lambda self: self.divisi_location_id.search
                                        ([('name','=','Division 1')]))
    date_request=fields.Date("Date Request",track_visibility='onchange')
    variety_id=fields.Many2one('estate.nursery.variety',required=True,track_visibility='onchange',
                               default=lambda self: self.variety_id.search
                                        ([('name','=','Dura')]))
    comment=fields.Text("Cause Pending")
    total_qty_pokok = fields.Integer("Quantity Pokok Seed",compute="_compute_total",track_visibility='onchange')
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
        self.action_move()
        return True

    @api.one
    def action_move(self):
        location_ids = set()
        blocklocation_ids = set()
        for item in self.requestline_ids:
            if item.location_id and item.qty_request > 0: # todo do not include empty quantity location
                location_ids.add(item.location_id.inherit_location_id)
                blocklocation_ids.add(item.block_location_id.inherit_location_id)

            for location in location_ids:
                qty_total_request = 0
                qty = self.env['estate.nursery.requestline'].search([('location_id.inherit_location_id', '=', location.id),
                                                                   ('request_id', '=', self.id)
                                                                   ])
                for i in qty:
                    qty_total_request += i.qty_request

                move_data = {
                    'product_id': item.batch_id.product_id.id,
                    'product_uom_qty': item.qty_request,
                    'origin':item.batch_id.name,
                    'product_uom': item.batch_id.product_id.uom_id.id,
                    'name': 'Move Seed to block.%s: %s'%(self.bpb_code,item.batch_id.name),
                    'date_expected': self.date_request,
                    'location_id': location.id,
                    'location_dest_id':item.block_location_id.inherit_location_id.id,
                    'state': 'done', # set to done if no approval required
                    'restrict_lot_id': item.batch_id.lot_id.id # required by check tracking product
                }
                move = self.env['stock.move'].create(move_data)
                move.action_confirm()
                move.action_done()
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
                division_value_name = division.block_location_id.name
                if division_value_name in temp.values():
                    error_msg = "Division for Block \"%s\" is set more than once " % division_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[division.id] = division_value_name
            return temp

    #onchange


class RequestLine(models.Model):

    _name = "estate.nursery.requestline"

    name=fields.Char("Requestline",related='request_id.name')
    request_id=fields.Many2one('estate.nursery.request',ondelete='cascade')
    batch_id = fields.Many2one('estate.nursery.batch',store=True)
    block_location_id = fields.Many2one('estate.block.template', ("Seed Location"),track_visibility='onchange',
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'planted'),
                                                  ('scrap_location', '=', False),
                                                  ],store=True)
    location_id = fields.Many2one('estate.block.template', "Plot",
                                    domain=[('estate_location', '=', True),
                                            ('estate_location_level', '=', '3'),
                                            ('estate_location_type', '=', 'nursery'),
                                            ('scrap_location', '=', False),
                                            ],
                                             help="Fill in location seed planted.",
                                             required=True,store=True)
    large_area = fields.Float("Luas Block",digits=(2,2),related='block_location_id.area_planted',readonly=True,store=True)
    qty_request = fields.Integer("Quantity Request",required=True,store=True)

    comment = fields.Text("Decription / Comment")

    #onchange or domain batch id for age more than 6
    @api.multi
    @api.onchange('batch_id')
    def _onchange_batch_id(self):
        #domain batch
        arrBatch=[]
        arrRecordBatch=[]
        batch = self.env['estate.nursery.batch'].search([('age_seed_range','>=',6),('qty_planted','>',0)])
        if self:
            if self.batch_id:
                batchTransferMn = self.env['estate.nursery.transfermn'].search([('batch_id.id','=',self.batch_id.id)])
                for b in batchTransferMn:
                    stockLocation = self.env['estate.block.template'].search([('id','=',b.location_mn_id[0].id)])
                    stock= self.env['stock.location'].search([('id','=',stockLocation.inherit_location_id[0].id)])
                    idlot= self.env['estate.nursery.batch'].search([('id','=',self.batch_id.id)])
                    qty = self.env['stock.quant'].search([('lot_id.id','=',idlot[0].lot_id.id),('location_id.id','=',stock[0].id)])
                    if qty[0].qty > 0:
                        arrRecordBatch.append(b.batch_id.id)
            for a in batch:
                arrBatch.append(a.id)
            return {
                'domain': {'batch_id': [('id','in',arrBatch)]}
            }

    #onchange location sesuai qty yang ada di plot setiap batch
    @api.multi
    @api.onchange('location_id','batch_id')
    def _onchange_location_id(self):
        arrLocation = []
        if self:
            batchTransferMn = self.env['estate.nursery.transfermn'].search([('batch_id.id','=',self.batch_id.id)])
            if self.batch_id:
                for b in batchTransferMn:
                    stockLocation = self.env['estate.block.template'].search([('id','=',b.location_mn_id[0].id)])
                    stock= self.env['stock.location'].search([('id','=',stockLocation.inherit_location_id[0].id)])
                    idlot= self.env['estate.nursery.batch'].search([('id','=',self.batch_id.id)])
                    qty = self.env['stock.quant'].search([('lot_id.id','=',idlot[0].lot_id.id),('location_id.id','=',stock[0].id)])
                    if qty[0].qty > 0:
                        arrLocation.append(b.location_mn_id.id)
            return {
                'domain': {
                           'location_id': [('id','=',arrLocation)]}
            }
        return True

    #constraint qty Request not moree than standard qty sph
    @api.one
    @api.constrains('qty_request','block_location_id','batch_id')
    def check_qty_request(self):
        qty_standard = self.block_location_id.qty_sph_standard
        # qty_do = self.inherit_location_id.qty_sph_do
        total=0
        batchTransferMn = self.env['estate.nursery.transfermn'].search([('batch_id.id','=',self.batch_id.id)])
        for b in batchTransferMn:
                    stockLocation = self.env['estate.block.template'].search([('id','=',b.location_mn_id[0].id)])
                    stock= self.env['stock.location'].search([('id','=',stockLocation.inherit_location_id[0].id)])
                    idlot= self.env['estate.nursery.batch'].search([('id','=',self.batch_id.id)])
                    qty = self.env['stock.quant'].search([('lot_id.id','=',idlot[0].lot_id.id),('location_id.id','=',stock[0].id)])
                    for a in qty:
                        total += a.qty
        if self.qty_request:
            if self.qty_request > qty_standard:
                    error_msg = "\"%s\" quantity is set not more than 126 " % self.block_location_id.name
                    raise exceptions.ValidationError(error_msg)
            # if self.qty_request > qty_do:
            #         error_msg = "\"%s\" quantity is set not more than 130 " % self.inherit_location_id.name
            #         raise exceptions.ValidationError(error_msg)
            if self.qty_request > total:
                    error_msg = "\"%s\" quantity is Maximal %s" % (self.block_location_id.name,total)
                    raise exceptions.ValidationError(error_msg)
            return True
