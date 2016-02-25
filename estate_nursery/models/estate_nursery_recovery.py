from openerp import models, fields, api, exceptions, _
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar


class NurseryRecovery(models.Model):

    _name ='estate.nursery.recovery'

    name=fields.Char(related="batch_id.name")
    recovery_code=fields.Char()
    selection_id=fields.Many2one('estate.nursery.selection',"Selection")
    batch_id= fields.Many2one('estate.nursery.batch')
    partner_id=fields.Many2one('res.partner')
    recovery_date=fields.Date("Recovery Date")
    recovery_line_ids = fields.One2many('estate.nursery.recoveryline','recovery_seed_id','Recovery Line')
    qty_recovery= fields.Integer("Quantity Recovery",related="selection_id.qty_recovery")
    qty_plant=fields.Integer()
    qty_normal=fields.Integer()
    qty_abnormal= fields.Integer("Quantity Abnormal",compute="_compute_total_abnormal")
    qty_plante=fields.Integer("Quantity Plant")
    qty_total=fields.Integer()
    culling_location_id = fields.Many2one('estate.block.template',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),
                                                  ('scrap_location', '=', True)]
                                          ,store=True,required=True)

    location_id = fields.Many2one('estate.block.template', "Bedengan",
                                    domain=[('estate_location', '=', True),
                                            ('estate_location_level', '=', '3'),
                                            ('estate_location_type', '=', 'nursery'),
                                            ('scrap_location', '=', False),
                                            ],
                                             help="Fill in location seed planted.",
                                             required=True,)
    state=fields.Selection([('draft','Draft'),
        ('confirmed', 'Confirmed'),('approved1','First Approval'),('approved2','Second Approval'),
        ('done', 'Transfere to Batch')],string="Recovery State")

    #Sequence Recovery code
    def create(self, cr, uid, vals, context=None):
        vals['recovery_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.recovery')
        res=super(NurseryRecovery, self).create(cr, uid, vals)
        return res

    @api.one
    @api.depends('recovery_line_ids')
    def _compute_total_abnormal(self):
        self.qty_abnormal = 0
        if self.recovery_line_ids:
            for item in self.recovery_line_ids:
                self.qty_abnormal += item.qty_abnormal
        return True

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
        # self.action_receive()
        self.state = 'done'

class RecoveryLine(models.Model):

    _name ='estate.nursery.recoveryline'

    name=fields.Char()
    recovery_seed_id=fields.Many2one('estate.nursery.recovery')
    cause_id=fields.Many2one('estate.nursery.cause')
    qty_abnormal=fields.Integer("Quantity Abnormal")
    location_type=fields.Many2one('stock.location',("location Last"),domain=[('name','=','Cleaving'),
                                                                             ('usage','=','inventory'),
                                                                             ],store=True,required=True,
                                  default=lambda self: self.location_type.search([('name','=','Cleaving')]))



