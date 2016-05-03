from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar


class ReturnSeed(models.Model):

    _name = "estate.nursery.returnseed"
    _description = "return seed after transfer to block"
    _inherit=['mail.thread']

    def _default_session(self):
        return self.env['estate.nursery.seeddo'].browse(self._context.get('active_id'))

    name=fields.Char()
    seeddo_id = fields.Many2one('estate.nursery.seeddo',store=True,default="_default_session")
    bpb_id = fields.Many2one('estate.nursery.request')
    returnseedline_ids = fields.One2many('estate.nursery.returnseedline','return_id','Return Line')
    return_date=fields.Date('Return Seed Date',store=True)
    total_qty_return=fields.Integer('Total Quantity Return',compute='_compute_total_qty_return',store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')], string="State",store=True)

    #workflow state
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
        self.action_receive()
        self.state = 'done'

    @api.one
    def action_receive(self):
        self.action_move()
        return True

    @api.one
    def action_move(self):
        location_ids = set()
        for item in self.returnseedline_ids:
            if item.location_id and item.qty_return > 0: # todo do not include empty quantity location
                location_ids.add(item.location_id.inherit_location_id)

            for location in location_ids:
                qty_total_return = 0
                qty = self.env['estate.nursery.returnseedline'].search([('location_id.inherit_location_id', '=', location.id),
                                                                   ('return_id', '=', self.id)
                                                                   ])
                for i in qty:
                    qty_total_return += i.qty_return

                move_data = {
                    'product_id': item.batch_id.product_id.id,
                    'product_uom_qty': item.qty_return,
                    'origin':item.batch_id.name,
                    'product_uom': item.batch_id.product_id.uom_id.id,
                    'name': 'Return Seed to Plot.%s: %s'%(self.bpb_id.bpb_code,item.batch_id.name),
                    'date_expected': self.return_date,
                    'location_id': item.block_location_id.inherit_location_id.id,
                    'location_dest_id':location.id,
                    'state': 'done', # set to done if no approval required
                    'restrict_lot_id': item.batch_id.lot_id.id # required by check tracking product
                }
                move = self.env['stock.move'].create(move_data)
                move.action_confirm()
                move.action_done()
        return True

    #onchange or domain

    # @api.multi
    # @api.onchange('bpb_id','seeddo_id')
    # def _onchange_bpb_id(self):
    #     # domain bpb id sesuai dengan list bpbp id yang ada di seeddo
    #     if self:
    #         bpblist = self.env['estate.nursery.request']
    #         arrBpblist = []
    #         for a in bpblist:
    #             arrBpblist.append(a.seeddo_id.id)
    #         print arrBpblist
    #         return {
    #             'domain': {'batch_id': [('id','in',arrBpblist)]}
    #         }
    #     # arrBpb = []
        # if self:
        #     # spbId = self.env['estate.nursery.returnseed'].search([]).seeddo_id
        #     # for a in self:
        #     #     print "test"
        #     #     print a
        #     bpbId = self.env['estate.nursery.request'].search([('seeddo_id','=',self.seeddo_id.id)]).id
        #     print"aaaaa"
        #     print bpbId
        #     # for a in bpbId:
        #     #     arrBpb.append(a.seeddo_id.id)
        #     # print"seeddo"
        #     #
        #     # print arrBpb

    #compute
    @api.multi
    @api.depends('total_qty_return','returnseedline_ids')
    def _compute_total_qty_return(self):
        # for compute qty return from line return seed
        self.total_qty_return = 0
        if self.returnseedline_ids:
            for qty in self.returnseedline_ids:
                self.total_qty_return += qty.qty_return
        return True

    #constrains
    @api.constrains('returnseedline_ids')
    def _constrains_returnseedline(self):
        #constraint for equalize line in seed_return between returnline to bpb line
        if self:
            countLine = 0
            countLineReturn = 0
            bpbLine = self.env['estate.nursery.request'].search([('id','=',self.bpb_id.id)])
            for item in bpbLine:
                countLine += len(item.requestline_ids)
            for itemline in self:
                countLineReturn += len(itemline.returnseedline_ids)
            if countLineReturn > countLine:
                error_msg = "Line Return Must be match with line in BPB"
                raise exceptions.ValidationError(error_msg)



class ReturnSeedLine(models.Model):

    _name ="estate.nursery.returnseedline"

    name=fields.Char()
    return_id = fields.Many2one('estate.nursery.returnseed',ondelete='cascade',store=True)
    batch_id = fields.Many2one('estate.nursery.batch',store=True)
    bpb_id = fields.Many2one('estate.nursery.request',store=True)
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
    qty_request = fields.Integer("Quantity Request",readonly=True,store=True)
    qty_return = fields.Integer("Quantity Return",required=True,store=True)
    qty_transfer = fields.Integer("Quantity Transfer",compute="_compute_qty_transfer",store=True)
    comment = fields.Text("Decription / Comment")

    #onchange or filter
    @api.multi
    @api.onchange('qty_request','block_location_id','batch_id','location_id')
    def _onchange_block_location(self):
        #domain block location , batch_id and location_id where bpb id in request line
        arrBlock = []
        arrBatch = []
        arrLocation =[]
        if self:
            bpbId =self.env['estate.nursery.requestline'].search([('request_id','=',self.bpb_id.id)])
            for a in bpbId:
                arrBlock.append(a.block_location_id.id)
                arrLocation.append(a.location_id.id)
                arrBatch.append(a.batch_id.id)
            if self.block_location_id and self.batch_id:
                qtyReq =self.env['estate.nursery.requestline'].search([('request_id','=',self.bpb_id.id)]).qty_request
                self.qty_request = qtyReq
        return {
                'domain': {'block_location_id': [('id','in',arrBlock)],
                           'batch_id':[('id','in',arrBatch)],
                           'location_id' :[('id','in',arrLocation)]},
            }

    #compute
    @api.multi
    @api.depends('qty_request','qty_return','qty_transfer')
    def _compute_qty_transfer(self):
        #compute qty transfer for spb
        self.qty_transfer = 0
        if self:
            self.qty_transfer = self.qty_request - int(self.qty_return)

    #constraint
    @api.constrains('qty_request','qty_return')
    def _constraint_qty_return(self):
        #for constraint qty_return not more than qty_request per BPB
        if self:
            if self.qty_return > self.qty_request:
                error_msg = "Quantity Return \"%s\" is not more than Qty %s" % (self.qty_return,self.qty_request)
                raise exceptions.ValidationError(error_msg)
        return True

