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
    return_date=fields.Datetime('Return Seed Date')
    total_qty_return=fields.Integer('Total Quantity Return')
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
        # self.action_receive()
        self.state = 'done'

    @api.one
    def action_receive(self):
        # self.action_move()
        return True

    #onchange or domain

    @api.multi
    @api.onchange('bpb_id','seeddo_id')
    def _onchange_bpb_id(self):
        # domain bpb id sesuai dengan list bpbp id yang ada di seeddo
        arrBpb = []
        if self:
            # spbId = self.env['estate.nursery.returnseed'].search([]).seeddo_id
            # for a in self:
            #     print "test"
            #     print a
            bpbId = self.env['estate.nursery.request'].search([('seeddo_id','=',self.seeddo_id.id)]).id
            print"aaaaa"
            print bpbId
            # for a in bpbId:
            #     arrBpb.append(a.seeddo_id.id)
            # print"seeddo"
            #
            # print arrBpb


class ReturnSeedLine(models.Model):

    _name ="estate.nursery.returnseedline"

    name=fields.Char()
    return_id = fields.Many2one('estate.nursery.returnseed')
    batch_id = fields.Many2one('estate.nursery.batch')
    block_location_id = fields.Many2one('estate.block.template', ("Seed Location"),track_visibility='onchange',
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'planted'),
                                                  ('scrap_location', '=', False),
                                                  ])
    location_id = fields.Many2one('estate.block.template', "Plot",
                                    domain=[('estate_location', '=', True),
                                            ('estate_location_level', '=', '3'),
                                            ('estate_location_type', '=', 'nursery'),
                                            ('scrap_location', '=', False),
                                            ],
                                             help="Fill in location seed planted.",
                                             required=True,)
    large_area = fields.Float("Luas Block",digits=(2,2),related='block_location_id.area_planted',readonly=True)
    qty_request = fields.Integer("Quantity Request",readonly=True)
    qty_return = fields.Integer("Quantity Return",required=True,store=True)
    qty_transfer = fields.Integer("Quantity Transfer",store=True)
    comment = fields.Text("Decription / Comment")

    #onchange or filter

    #constraint