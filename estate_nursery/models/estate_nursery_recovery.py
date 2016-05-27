from openerp import models, fields, api, exceptions, _
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar


class NurseryRecovery(models.Model):

    _name ='estate.nursery.recovery'
    _inherit = ['mail.thread']

    def _default_session(self):
        return self.env['estate.nursery.batch'].browse(self._context.get('active_id'))

    name=fields.Char(related="batch_id.name")
    recovery_code=fields.Char()
    batch_id= fields.Many2one('estate.nursery.batch','batch',default=_default_session)
    partner_id=fields.Many2one('res.partner')
    stage_id = fields.Many2one('estate.nursery.stage','Stage Selection',required=True)
    step_id = fields.Many2one('estate.nursery.steprecovery','Step Recovery',store=True,required=True)
    recovery_date=fields.Date("Recovery Date",store=True)
    date_planted = fields.Date("Date Planted",store=True,readonly=True)
    age_seed_recovery = fields.Integer("Age Seed Recovery",compute='_compute_age_seed',store=True)
    age_seed = fields.Integer('Age Seed')
    recovery_line_ids = fields.One2many('estate.nursery.recoveryline','recovery_seed_id','Recovery Line')
    qty_recovery= fields.Integer("Quantity Recovery",)
    qty_plant=fields.Integer()
    qty_normal=fields.Integer(compute="_compute_total_normal",store=True, track_visibility='onchange')
    qty_dead = fields.Integer(compute="_compute_total_normal",store=True)
    qty_abnormal= fields.Integer("Quantity Variant",compute="_compute_abnormal" , track_visibility='onchange',store=True)
    qty_plante=fields.Integer("Quantity Seed Planted Batch" , track_visibility='onchange')
    qty_total = fields.Integer("Result Quantity",compute="_compute_total_normal",store=True, track_visibility='onchange')
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


    #Compute Seed
    @api.one
    @api.depends('recovery_line_ids','qty_normal','qty_plante','qty_recovery','qty_dead')
    def _compute_abnormal(self):
        self.qty_dead= 0
        self.qty_normal=0
        if self.recovery_line_ids:
            if self.qty_dead and self.qty_normal:
                self.qty_abnormal= int(self.qty_recovery)-(int(self.qty_dead)+self.qty_normal)
        return True


    #constraint for Quantity normal set nor more than quanity recovery
    @api.constrains('qty_normal','qty_recovery')
    def _constraint_qty_normal(self):
        recoveryline = self.env['estate.nursery.recoveryline'].search([('recovery_seed_id', '=', self.id)])
        if recoveryline:
            for obj in recoveryline:
                seed_qty = obj.qty_normal

                if seed_qty > self.qty_recovery:
                        raise ValidationError("Quantity Normal Not More Than Seed Recovery !")

    #constraint for Quantity Dead set nor more than quanity recovery
    @api.constrains('qty_normal','qty_recovery')
    def _constraint_qty_normal(self):
        recoveryline = self.env['estate.nursery.recoveryline'].search([('recovery_seed_id', '=', self.id)])
        if recoveryline:
            for obj in recoveryline:
                seed_qty = obj.qty_dead

                if seed_qty > self.qty_recovery:
                        raise ValidationError("Quantity Dead Not More Than Seed Recovery !")

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
            if item.location_id and item.qty_dead > 0: # todo do not include empty quantity location
                location_ids.add(item.location_id.inherit_location_id)

            for location in location_ids:
                qty_total_dead_recovery = 0
                qty = self.env['estate.nursery.recoveryline'].search([('location_id.inherit_location_id', '=', location.id),
                                                                   ('recovery_seed_id', '=', self.id)
                                                                   ])
                for i in qty:
                    qty_total_dead_recovery = i.qty_dead

                move_data = {
                    'product_id': self.batch_id.product_id.id,
                    'product_uom_qty': item.qty_dead,
                    'origin':self.recovery_code,
                    'product_uom': self.batch_id.product_id.uom_id.id,
                    'name': 'Selection Recovery Dead.%s: %s'%(self.recovery_code,self.batch_id.name),
                    'date_expected': self.recovery_date,
                    'location_id': item.location_type.id,
                    'location_dest_id':self.culling_location_id.inherit_location_id.id,
                    'state': 'confirmed', # set to done if no approval required
                    'restrict_lot_id': self.batch_id.lot_id.id # required by check tracking product
                }
                move = self.env['stock.move'].create(move_data)
                move.action_confirm()
                move.action_done()


        batch_ids = set()
        for itembatch in self.recovery_line_ids:
            if  itembatch.location_id and itembatch.qty_normal > 0:
                batch_ids.add(itembatch.location_id.inherit_location_id)

            for batchrecovery in batch_ids:
                qty_total_normal_recovery = 0
                locationrecov = self.env['estate.nursery.recoveryline'].search([('location_id.inherit_location_id', '=', batchrecovery.id),
                                                                        ('recovery_seed_id', '=', self.id)])
                for i in locationrecov:
                    qty_total_normal_recovery = i.qty_normal

                move_data = {
                        'product_id': self.batch_id.product_id.id,
                        'product_uom_qty': itembatch.qty_normal,
                        'origin':self.recovery_code,
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
    @api.depends('recovery_line_ids','qty_normal','qty_dead','qty_plante','qty_total')
    def _compute_total_normal(self):
        self.qty_total = 0
        if self.recovery_line_ids:
            for item in self.recovery_line_ids:
                self.qty_normal += item.qty_normal
                self.qty_dead += item.qty_dead
            self.qty_total = int(self.qty_plante) + self.qty_normal
        return True

    @api.depends('age_seed_recovery','recovery_date','date_planted','age_seed')
    def _compute_age_seed(self):
        res={}
        fmt = '%Y-%m-%d'
        if self.age_seed and self.recovery_date:
            from_date = self.date_planted
            age_seed = self.age_seed
            to_date = self.recovery_date
            conv_fromdate = datetime.strptime(str(from_date), fmt)
            conv_todate = datetime.strptime(str(to_date), fmt)
            d1 = conv_fromdate.month
            d2 = conv_todate.month
            rangeyear = conv_todate.year
            rangeyear1 = conv_fromdate.year
            rsult = rangeyear - rangeyear1
            yearresult = rsult * 12
            self.age_seed_recovery =((d2 + yearresult) - d1)-int(age_seed)
        return res

class RecoveryLine(models.Model):

    _name ='estate.nursery.recoveryline'

    name=fields.Char()
    recovery_seed_id=fields.Many2one('estate.nursery.recovery')
    stageline_a_id = fields.Many2one('estate.nursery.stage')
    qty_normal=fields.Integer("Quantity Normal",required=True,store=True)
    qty_dead = fields.Integer("Quantity Dead",required=True,store=True)
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
    @api.onchange('qty_abnormal','recovery_seed_id')
    def change_abnormal(self):
        if self.qty_dead:
            self.qty_abnormal = self.recovery_seed_id.qty_abnormal

    @api.one
    @api.onchange('qty_normal','recovery_seed_id')
    def change_normal(self):
        if self.qty_dead:
            self.qty_normal = self.recovery_seed_id.qty_normal

    @api.multi
    @api.onchange('stageline_a_id','location_id','recovery_seed_id')
    def change_location(self):
        self.stageline_a_id = self.recovery_seed_id.stage_id
        if self:
            arrRecoverySeed = []
            if self.stageline_a_id.code == 'PN':
                batchTransferPn =self.env['estate.nursery.batchline'].search([('batch_id.id','=',self.recovery_seed_id.batch_id.id),
                                                                              ('location_id.id','!=',False)])
                for a in batchTransferPn:
                    arrRecoverySeed.append(a.location_id.id)
            elif self.stageline_a_id.code == 'MN':
                batchTransferMn = self.env['estate.nursery.transfermn'].search([('batch_id.id','=',self.recovery_seed_id.batch_id.id)])
                for b in batchTransferMn:
                    stockLocation = self.env['estate.block.template'].search([('id','=',b.location_mn_id[0].id)])
                    stock= self.env['stock.location'].search([('id','=',stockLocation.inherit_location_id[0].id)])
                    idlot= self.env['estate.nursery.batch'].search([('id','=',self.recovery_seed_id.batch_id.id)])
                    qty = self.env['stock.quant'].search([('lot_id.id','=',idlot[0].lot_id.id),('location_id.id','=',stock[0].id)])
                    if qty[0].qty > 0:
                        arrRecoverySeed.append(b.location_mn_id.id)
            return {
                'domain': {'location_id': [('id','in',arrRecoverySeed)]},
            }
        return True




class StepRecovery(models.Model):

    _name = 'estate.nursery.steprecovery'

    name=fields.Char()
    stage_id=fields.Many2one('estate.nursery.stage')



