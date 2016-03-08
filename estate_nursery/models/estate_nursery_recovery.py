from openerp import models, fields, api, exceptions, _
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar


class NurseryRecovery(models.Model):

    _name ='estate.nursery.recovery'
    _inherit = ['mail.thread']
    _inherits =  {'estate.nursery.batch': 'batch_id'}

    name=fields.Char(related="batch_id.name")
    recovery_code=fields.Char()
    selection_id=fields.Many2one('estate.nursery.selection','Selection',domain=[('stage_id','=', 2 )])
    batch_id= fields.Many2one('estate.nursery.batch','batch')
    partner_id=fields.Many2one('res.partner')
    recovery_date=fields.Date("Recovery Date")
    recovery_line_ids = fields.One2many('estate.nursery.recoveryline','recovery_seed_id','Recovery Line')
    qty_recovery= fields.Integer("Quantity Recovery",compute="_compute_qty_recovery")
    qty_plant=fields.Integer()
    qty_normal=fields.Integer(compute="_compute_total_normal",store=True, track_visibility='onchange')
    qty_abnormal= fields.Integer("Quantity Abnormal",compute="_compute_abnormal" , track_visibility='onchange')
    qty_plante=fields.Integer("Quantity Seed Planted Batch" , track_visibility='onchange')
    qty_total = fields.Integer( "Result Quantity",compute="_compute_total", track_visibility='onchange')
    culling_location_id = fields.Many2one('estate.block.template',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),
                                                  ('scrap_location', '=', True)]
                                          ,store=True,required=True)
    state=fields.Selection([('draft','Draft'),
        ('confirmed', 'Confirmed'),('approved1','First Approval'),('approved2','Second Approval'),
        ('done', 'Transfere to Batch')],string="Recovery State")

    #Sequence Recovery code
    def create(self, cr, uid, vals, context=None):
        vals['recovery_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.recovery')
        res=super(NurseryRecovery, self).create(cr, uid, vals)
        return res

    @api.one
    @api.depends('selection_id')
    def _compute_qty_recovery(self):
        self.qty_recovery = 0
        if self.selection_id:
            for qty in self.selection_id:
                self.qty_recovery += qty.qty_recovery
        return True

    #Compute Seed
    @api.one
    @api.depends('qty_normal','qty_plante','qty_recovery')
    def _compute_abnormal(self):
        if self.recovery_line_ids:
            self.qty_abnormal= int(self.qty_recovery)-self.qty_normal
        return True

    @api.one
    @api.depends('qty_normal','qty_plante')
    def _compute_total(self):
        if self.qty_normal and self.qty_plante:
            self.qty_total = int(self.qty_plante) + self.qty_normal


    #state for Cleaving
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
        """Approved Selection is planted Seed to batch."""
        self.action_receive()
        self.state = 'done'

    @api.one
    def action_receive(self):
        self.qty_normal = 0
        for itembatch in self.recovery_line_ids:
            self.qty_normal += itembatch.qty_normal
        self.write({'qty_normal':self.qty_normal})
        self.action_move()

    @api.one
    def action_move(self):
        location_ids = set()
        for item in self.recovery_line_ids:
            if item.location_id and item.qty_abnormal > 0: # todo do not include empty quantity location
                location_ids.add(item.location_id.inherit_location_id)

        for location in location_ids:
            qty_total_abnormal_recovery = 0
            qty = self.env['estate.nursery.recoveryline'].search([('location_id.inherit_location_id', '=', location.id),
                                                                   ('recovery_seed_id', '=', self.id)
                                                                   ])
            for i in qty:
                qty_total_abnormal_recovery += i.qty_abnormal

            move_data = {
                'product_id': self.batch_id.product_id.id,
                'product_uom_qty': qty_total_abnormal_recovery,
                'product_uom': self.batch_id.product_id.uom_id.id,
                'name': 'Selection Recovery Abnormal.%s: %s'%(self.recovery_code,self.batch_id.name),
                'date_expected': self.recovery_date,
                'location_id': item.location_type.id,
                'location_dest_id':self.culling_location_id.inherit_location_id.id,
                'state': 'confirmed', # set to done if no approval required
                'restrict_lot_id': self.lot_id.id # required by check tracking product
            }
            move = self.env['stock.move'].create(move_data)
            move.action_confirm()
            move.action_done()


        batch_ids = set()
        for itembatch in self.recovery_line_ids:
            if  itembatch.location_id and itembatch.qty_abnormal > 0:
                batch_ids.add(itembatch.location_id.inherit_location_id)

            for batchrecovery in batch_ids:

                trash = self.env['estate.nursery.recoveryline'].search([('location_id.inherit_location_id', '=', batchrecovery.id),
                                                                        ('recovery_seed_id', '=', self.id)])

            move_data = {
                        'product_id': self.batch_id.product_id.id,
                        'product_uom_qty': self.qty_normal,
                        'product_uom': self.batch_id.product_id.uom_id.id,
                        'name': 'Move Normal Seed  %s for %s:'%(self.recovery_code,self.batch_id.name),
                        'date_expected': self.recovery_date,
                        'location_id': itembatch.location_type.id,
                        'location_dest_id': itembatch.location_id.inherit_location_id.id,
                        'state': 'confirmed', # set to done if no approval required
                        'restrict_lot_id': self.batch_id.lot_id.id # required by check tracking product
                 }
            move = self.env['stock.move'].create(move_data)
            move.action_confirm()
            move.action_done()
        return True

    @api.one
    @api.depends('recovery_line_ids')
    def _compute_total_normal(self):
        if self.recovery_line_ids:
            for item in self.recovery_line_ids:
                self.qty_normal += item.qty_normal
        return True

class RecoveryLine(models.Model):

    _name ='estate.nursery.recoveryline'

    name=fields.Char()
    recovery_seed_id=fields.Many2one('estate.nursery.recovery')
    qty_normal=fields.Integer("Quantity Normal",required=True)
    qty_abnormal=fields.Integer("Quantity Abnormal")
    location_type=fields.Many2one('stock.location',("location Last"),domain=[('name','=','Cleaving'),
                                                                             ('usage','=','inventory'),
                                                                             ],store=True,required=True,
                                  default=lambda self: self.location_type.search([('name','=','Cleaving')]))
    location_id = fields.Many2one('estate.block.template', "Bedengan",
                                    domain=[('estate_location', '=', True),
                                            ('estate_location_level', '=', '3'),
                                            ('estate_location_type', '=', 'nursery'),
                                            ('scrap_location', '=', False),
                                            ],
                                             help="Fill in location seed planted.",
                                             required=True,)
    @api.one
    @api.onchange('qty_abnormal')
    def change_abnormal(self):
        self.qty_abnormal = self.recovery_seed_id.qty_abnormal
        self.write({'qty_abnormal' : self.qty_abnormal})

