# -*- coding: utf-8 -*-

import math
import re
import time


from openerp import models, fields, api, exceptions, _
from datetime import datetime, date
from openerp.exceptions import ValidationError


from dateutil.relativedelta import *
import calendar

def ean_checksum(eancode):
    """returns the checksum of an ean string of length 13, returns -1 if the string has the wrong length"""
    if len(eancode) != 13:
        return -1
    oddsum=0
    evensum=0
    total=0
    eanvalue=eancode
    reversevalue = eanvalue[::-1]
    finalean=reversevalue[1:]

    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total=(oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) %10
    return check

def check_ean(eancode):
    """returns True if eancode is a valid ean13 string, or null"""
    if not eancode:
        return True
    if len(eancode) != 13:
        return False
    try:
        int(eancode)
    except:
        return False
    return ean_checksum(eancode) == int(eancode[-1])

class EstateLocation(models.Model):
    """Extend Location for Nursery Location"""
    _inherit = 'stock.location'


    qty_seed = fields.Integer(string="Seed Quantity",)
    stage_id = fields.Many2one('estate.nursery.stage', "Nursery Stage", ondelete='set null')


class Seed(models.Model):
    _inherit = 'product.template'

    seed = fields.Boolean("Seed Product", help="Included at Seed Management.", default=False)
    # age_purchased = fields.Integer("Purchased Age", help="Fill in age of seed in month") # deprecated move to stock_quant
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety",
                                 help="Select Seed Variety.")
    @api.multi
    @api.onchange('variety_id','seed')
    def _onchange_variety_id(self):
        if self:
            if self.seed == True:
                return {
                    'domain':{'variety_id': [('name','=','Tenera')]}
                }
            else:
                return False



class Stage(models.Model):
    """
    Seed nursery has two kind of method. First, single stage. Second, double stage (common).
    """
    _name = 'estate.nursery.stage'

    name = fields.Char("Nursery Stage", required=True)
    code = fields.Char("Short Name", help="Use for reporting label purposes.", size=3)
    sequence = fields.Integer("Sequence No")
    age_minimum = fields.Integer("Minimum Age", help="Minimum age required to be at this stage. 0 is unlimited.")
    age_maximum = fields.Integer("Maximum Age", help="Maximum age required to be at this stage. 0 is unlimited.")
    selectionstage_id =fields.Many2one("estate.nursery.selectionstage")
    cause_id = fields.Many2one('estate.nursery.cause')


class Variety(models.Model):
    """Seed Variety"""
    _name = 'estate.nursery.variety'

    name = fields.Char(string="Variety Name")
    code = fields.Char(string="Short Name", help="Use for reporting label purposes.", size=3)
    comment = fields.Text(string="Additional Information")
    active = fields.Boolean("Planting Allowed", default=True, help="Seed Variety allowed to be planted.")


class Progeny(models.Model):
    """Seed Progeny"""
    _name = 'estate.nursery.progeny'

    name = fields.Char(string="Progeny Name")
    code = fields.Char(string="Short Name", help="Use for reporting label purposes.", size=3)
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety")
    comment = fields.Text(string="Additional Information")
    active = fields.Boolean("Planting Allowed", default=True, help="Seed Progeny allowed to be planted.")
    supplier_id = fields.Many2one('res.partner', string="Supplier", domain=[('supplier','=',True)])
    height_tree = fields.Float('Tree Height', digits=(2,2))
    height_growth_speed= fields.Float('Average Growth Speed', help='Average growth speed per metric/year', digts=(2,2))
    age_harvest = fields.Integer('Harvested Age', help='Ripe Age in Month')
    weight_bunch = fields.Float('Average Weight FBR', help='Average weight in kilograms.')
    oil_production = fields.Float('Oil Production', help='Average oil production per tonne/hectare/year', digits=(2,2))


class Condition(models.Model):
    _name = 'estate.nursery.condition'

    name = fields.Char("Box/Plastic Condition")
    condition_category = fields.Selection([('1','Box'),('2','Bag/Plastic')], "Category")
    broken = fields.Boolean("Broken Condition", help="Condition marked as broken will go to Culling.", default=False)
    sequence = fields.Integer("Sequence No")
    comment = fields.Text("Additional Information")

class Batch(models.Model):
    """Delegation Inheritance Product for Seed Batch. Created from Transfer."""

    def return_action_to_open(self, cr, uid, ids, context=None):
        """ This opens the xml view specified in xml_id for the current Batch """
        if context is None:
            context = {}
        if context.get('xml_id'):
            res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid ,'estate_nursery', context['xml_id'], context=context)
            res['context'] = context
            res['context'].update({'default_batch_id': ids[0]})
            res['domain'] = [('batch_id','=', ids[0])]
            return res
        return False


    _name = 'estate.nursery.batch'
    _description = "Seed Batch"
    _inherit=['mail.thread']
    _inherits = {'stock.production.lot': 'lot_id'}

    partner_id = fields.Many2one('res.partner')
    name = fields.Char(_("Batch No"), readonly= True)
    culling_id=fields.Many2one("estate.nursery.culling")
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)])
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety", required=True, ondelete="restrict")
    product_id = fields.Many2one('product.product', "Product", related="lot_id.product_id")
    picking_id = fields.Many2one('stock.picking', "Picking", readonly=True ,)
    culling_location_id = fields.Many2one('estate.block.template', _("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),
                                                  ('scrap_location', '=', True),
                                                  ])
    kebun_location_id = fields.Many2one('estate.block.template', _("Estate Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '1'),
                                                  ],
                                        default=lambda self: self.kebun_location_id.search([('name','=','LYD')]))
    stage_id=fields.Many2one("estate.nursery.stage")
    selection_id = fields.Many2one("estate.nursery.selection",'Selection Id')

    date_received = fields.Date("Received Date",required=False,readonly=True)
    date_planted = fields.Date("Planted Date",required=False,readonly=False)
    age_seed_range=fields.Integer("Seed Age",compute='_compute_age_total',readonly=True,store=True,track_visibility='onchange')
    age_seed_planted=fields.Integer("Seed Age",compute='_compute_age_planted',store=True)
    age_seed = fields.Integer("Seed Age Received",store=True)
    selection_count = fields.Integer("Selection Seed Count", compute="_get_selection_count")
    comment = fields.Text("Additional Information",track_visibility='onchange')
    month=fields.Integer("Month Rule",compute="_rule_month",store=True)
    qty_received = fields.Integer("Quantity Received")
    qty_normal = fields.Integer("Normal Seed Quantity",track_visibility='onchange',store=True)
    qty_single= fields.Integer("single Seed Quantity",compute='_compute_single',store=True)
    qty_double=fields.Integer("Double Seed Quantity",compute='_compute_double',store=True)
    qty_abnormal=fields.Integer("Abnormal Seed Quantity",track_visibility='onchange',store=True)
    qty_normal_double=fields.Integer("Normal After Cleaving")
    qty_abnormal_double=fields.Integer("Abnormal After Double")
    qty_recovery= fields.Integer(compute="_compute_recovery")
    qty_planted = fields.Integer(_("Planted"), compute='_compute_total',store=True)
    qty_planted_temp = fields.Integer(_("Planted"), compute='_compute_total_temp',store=True)
    total_selection_abnormal=fields.Integer(compute="_compute_tot_abnormal",store=True)

    cleaving_ids=fields.One2many('estate.nursery.cleaving','batch_id',)
    cleavingln_ids=fields.One2many('estate.nursery.cleavingln','batch_id',readonly=True)
    recovery_ids=fields.One2many('estate.nursery.recovery','batch_id','Recovery',)
    batchline_ids = fields.One2many('estate.nursery.batchline', 'batch_id', _("Seed Boxes")) # Detailed selection
    selection_ids = fields.One2many('estate.nursery.selection', 'batch_id', _("Selection"))
    selectionline_ids = fields.One2many('estate.nursery.selectionline', 'batch_id', _("Selectionline"))# Detaileld selection
    transfermn_ids =fields.One2many('estate.nursery.transfermn','batch_id',"Transfer Line")

    status =fields.Boolean("Status test")
    status_age=fields.Boolean("Status age")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),('selection','Selection Nursery'),
        ('recovery','Recovery Seed'),('cleaving','Cleaving Seed Polytone'),
        ('tfmain','Transfer Main Nursery'),
        ('done', 'Selection Seed Receiving')], string="State")

    @api.multi
    def action_view_request_mn(self):
        course_form = self.env.ref('estate_nursery.view_form_transferto_mn', False)
        return {
            'name': 'New request',
            'type': 'ir.actions.act_window',
            'res_model': 'estate.nursery.transfermn',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'views': [(course_form.id, 'form')],
            'view_id': 'course_form.id',
            }


    @api.one
    def action_draft(self):
        """Set Batch State to Draft."""
        # self.ensure_one()
        self.state = 'draft'

    @api.one
    def action_confirmed(self):
        """Set Batch state to Confirmed."""
        # self.ensure_one()
        self.state = 'confirmed'


    @api.one
    def action_approved(self):
        """Approved Batch is planted Seed."""
        # self.ensure_one()
        self.action_receive()
        self.state = 'done'


    @api.one
    def action_transfer_mainnursery(self):
        """Set Batch state to Transfer to Main nursery."""
        # self.ensure_one()
        self.state='tfmain'

    @api.one
    def action_receive(self):
        """Count quantity of seed received and planted."""
        # self.ensure_one()
        self.qty_normal = 0
        self.qty_abnormal = 0
        for item in self.batchline_ids:
            self.qty_normal += item.subtotal_normal
            self.qty_abnormal += item.subtotal_abnormal
        self.write({'nursery_stage': '0' ,'qty_normal': self.qty_normal, 'qty_abnormal': self.qty_abnormal})

        self.action_planted()
        return True

    @api.one
    def action_selection_next(self):
        """Set Batch State to next selection"""
        # self.ensure_one()
        if int(self.nursery_stage) < 6:
            self.nursery_stage = str(int(self.nursery_stage)+1)


    @api.one
    def action_planted(self):
        """
        Planted do two actions:
        1. Set state to Seed Planted.
        2. Move quantity of seed to production location.
        3. Move quantity of abnormal seed to culling location.
        """
        # self.ensure_one()
        self.nursery_stage = '1'

        # Get unique location of planted location
        location_ids = set()
        for item in self.batchline_ids:
            if item.location_id and item.qty_planted > 0: # todo do not include empty quantity location
                location_ids.add(item.location_id.inherit_location_id)

        # Move quantity normal seed
        for location in location_ids:
            qty_total_planted = 0
            bags = self.env['estate.nursery.batchline'].search([('location_id.inherit_location_id', '=', location.id),
                                                                   ('batch_id', '=', self.id)])
            for i in bags:
                qty_total_planted += i.qty_planted

            move_data = {
                'product_id': self.lot_id.product_id.id,
                'product_uom_qty': qty_total_planted,
                'product_uom': self.lot_id.product_id.uom_id.id,
                'name': 'Planted: %s' % self.lot_id.product_id.display_name,
                'date_expected': self.date_planted,
                'location_id': self.picking_id.location_dest_id.id,#Harus di tanyakan
                'location_dest_id': location.id,
                'state': 'confirmed', # set to done if no approval required
                'restrict_lot_id': self.lot_id.id # required by check tracking product
            }

            move = self.env['stock.move'].create(move_data)
            move.action_confirm()
            move.action_done()

        # Move quantity abnormal seed
        if self.qty_abnormal > 0:
            move_data = {
                'product_id': self.lot_id.product_id.id,
                'product_uom_qty': self.qty_abnormal,
                'product_uom': self.lot_id.product_id.uom_id.id,
                'name': 'Selection: %s' % self.lot_id.product_id.display_name,
                'date_expected': self.date_planted,
                'location_id': self.picking_id.location_dest_id.id,
                'location_dest_id': self.culling_location_id.inherit_location_id.id,
                'state': 'confirmed', # set to done if no approval required
                'restrict_lot_id': self.lot_id.id # required by check tracking product
            }

            move = self.env['stock.move'].create(move_data)
            move.action_confirm()
            move.action_done()

        return True


    # set constraint to date received to date planted
    @api.multi
    @api.constrains('date_received','date_planted')
    def _check_date(self):
        for obj in self:
            start_date = obj.date_received
            end_date = obj.date_planted

            if start_date and end_date:
                DATETIME_FORMAT = "%Y-%m-%d"  ## Set your date format here
                from_dt = datetime.strptime(start_date, DATETIME_FORMAT)
                to_dt = datetime.strptime(end_date, DATETIME_FORMAT)
                if to_dt < from_dt:
                     raise ValidationError("Planted Date Should be Greater than Received Date!" )

    # Constraint to selection stage more than 1
    @api.multi
    @api.constrains('selection_ids')
    def _constrains_selectionstage_selection(self):
        self.ensure_one()
        if self.selection_ids:
            temp={}
            for stage in self.selection_ids:
                stage_value_name = stage.selectionstage_id.name
                if stage_value_name in temp.values():
                    error_msg = "Selection Stage Seed \"%s\" is set more than once " % stage_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[stage.id] = stage_value_name
            return temp

    #constraint to recovery if step recovery selec not more than 1 for recovery
    @api.multi
    @api.constrains('recovery_ids')
    def _constrains_step_selection(self):
        self.ensure_one()
        if self.recovery_ids:
            temp={}
            for step in self.recovery_ids:
                step_value_name = step.step_id.name
                if step_value_name in temp.values():
                    error_msg = "Recovery Step Seed \"%s\" is set more than once " % step_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[step.id] = step_value_name
            return temp

    #Constraint to date selection  not more than selection older
    @api.multi
    @api.constrains('selection_ids')
    def _constrains_date_selection(self):
        self.ensure_one()
        if self.selection_ids:
            temp={}
            for date in self.selection_ids:
                date_value_name = date.selection_date
                if date_value_name in temp.values():
                    error_msg = "Selection Date  is set more than Selection Older "
                    raise exceptions.ValidationError(error_msg)
                temp[date.id] = date_value_name
            return temp

    # #constraint age_cleaving
    # @api.multi
    # @api.constrains('cleaving_ids')
    # def _constraints_date_cleaving(self):
    #     if self.cleaving_ids:
    #         for age in self.cleaving_ids:
    #             age_seed_clv = age.age_seed_clv
    #             if age_seed_clv < self.age_seed_range:
    #                 error_msg = "Age Seed Cleaving is set more than Age seed batch !!"
    #                 raise exceptions.ValidationError(error_msg)
    #         return True
    #
    # #constraint Age recovery
    # @api.one
    # @api.constrains('recovery_ids')
    # def _constraints_date_recovery(self):
    #     if self.recovery_ids:
    #         for age in self.recovery_ids:
    #             age_seed_clv = age.age_seed_recovery
    #             if age_seed_clv < self.age_seed_range:
    #                 error_msg = "Age Seed Recovery is set more than Age seed batch!!"
    #                 raise exceptions.ValidationError(error_msg)
    #         return True


    # set constraint to Quantity in batch line not more than quantity DO
    @api.multi
    @api.constrains('batchline_ids')
    def _check_quantity_batchline(self):
        batchlinebag = self.env['estate.nursery.batchline'].search([('flag_bag', '=', True),
                                                                   ('batch_id', '=', self.id)])
        if batchlinebag:
            for obj in batchlinebag:
                seed_qty = obj.seed_qty
                qty_single = obj.qty_single
                qty_double = obj.qty_double
                qty_fungus = obj.qty_fungus
                qty_broken = obj.qty_broken
                qty_normal = obj.subtotal_normal
                qty_abnormal = obj.subtotal_abnormal
                qty_dead = obj.qty_dead
                qty_planted = obj.qty_planted

                if seed_qty < qty_single:
                        raise ValidationError("Quantity Single Should be Greater than Seed DO !")
                elif qty_abnormal > seed_qty:
                        raise ValidationError("Quantity Total Abnormal not matched with Quantity Planted")
                # elif qty_normal > qty_planted:
                #         raise ValidationError("Quantity Total Normal not matched with Quantity Planted")
                elif seed_qty < qty_double:
                        raise ValidationError("Quantity Double Should be Greater than Seed DO !")
                elif seed_qty < qty_fungus:
                        raise ValidationError("Quantity Fungus Should be Greater than Seed DO !")
                elif seed_qty < qty_broken:
                        raise ValidationError("Quantity Broken Should be Greater than Seed DO !")
                elif seed_qty < qty_dead:
                        raise ValidationError("Quantity Dead Should be Greater than Seed DO !")
                elif seed_qty < qty_planted:
                        raise ValidationError("Quantity Planted Should be Greater than Seed DO !")
                elif qty_planted < qty_single:
                        raise ValidationError("Quantity Planted Should be Same than Qty_single !")
            return True

    # Constraint for not variance after selection
    @api.multi
    @api.constrains('batchline_ids')
    def _check_qty_variance(self):
        self.ensure_one()
        batchlinebag = self.env['estate.nursery.batchline'].search([('flag_bag', '=', True),
                                                                   ('batch_id', '=', self.id)])
        if batchlinebag:
            for obj in batchlinebag:
                varselec = obj.selection_do_var
                varplanting = obj.planting_selection_var

                if varselec :
                        if varselec > 1:
                            error_msg = "Selection Variance \"%d\" Quantity is Different between Selection and DO  " % varselec
                            raise exceptions.ValidationError(error_msg)
                if varplanting:
                        if varplanting > 1:
                            error_msg = "Planting Variance \"%d\" Quantity is Different between Planting,Do or Selection " % varplanting
                            raise exceptions.ValidationError(error_msg)
            return True


    #count selection
    @api.multi
    @api.depends('selection_ids')
    def _get_selection_count(self):
        self.ensure_one()
        for r in self:
            r.selection_count = len(r.selection_ids)

    # monthrange
    @api.multi
    @api.depends('month')
    def _rule_month(self):
        self.ensure_one()
        self.month =int(12)

    #total selection abnormal
    @api.multi
    @api.depends("selection_ids")
    def _compute_tot_abnormal(self):
        self.ensure_one()
        self.total_selection_abnormal = 0
        if self.selection_ids:
            for a in self.selection_ids:
                self.total_selection_abnormal += a.qty_abnormal
            return True

    #get Qty Recovery
    @api.one
    @api.depends('selection_ids','recovery_ids')
    def _compute_recovery(self):
        self.qty_recovery=0
        if self.selection_ids:
            for recovery in self.selection_ids:
                self.qty_recovery += recovery.qty_recovery
            if self.recovery_ids:
                for item_recovery in self.recovery_ids:
                    self.qty_recovery -= item_recovery.qty_normal
                if self.recovery_ids.qty_dead:
                    for totalnormal in self.recovery_ids:
                        self.qty_recovery -= totalnormal.qty_dead
        return True

    #get single qty
    @api.multi
    @api.depends("batchline_ids")
    def _compute_single(self):
        self.ensure_one()
        self.qty_single = 0
        if self.batchline_ids:
            for a in self.batchline_ids:
                self.qty_single += a.qty_single
        return True

    #get double qty
    @api.multi
    @api.depends("batchline_ids")
    def _compute_double(self):
        self.ensure_one()
        self.qty_double = 0
        if self.batchline_ids:
            for item in self.batchline_ids:
                self.qty_double += item.qty_double
        return True


    #computed seed planted
    @api.one
    @api.depends('batchline_ids','selection_ids','cleaving_ids','recovery_ids')
    def _compute_total(self):
        self.qty_planted = 0
        if self.batchline_ids:
            for item in self.batchline_ids:
                self.qty_planted += item.qty_planted
            if self.selection_ids:
                for qty_selection in self.selection_ids:
                    try:
                        self.qty_planted -= qty_selection.qty_recoveryabn
                    except:
                        self.qty_planted
            if self.cleaving_ids :
                for totalcleaving in self.cleaving_ids:
                    self.qty_planted -= totalcleaving.qty_doublebatch
                if self.cleaving_ids.qty_normal:
                    for totalnormal in self.cleaving_ids:
                        self.qty_planted += totalnormal.qty_normal
            if self.recovery_ids:
                if self.recovery_ids.qty_normal:
                    for qty_recovery in self.recovery_ids:
                        self.qty_planted += qty_recovery.qty_normal
        return True

    @api.multi
    @api.depends('batchline_ids',)
    def _compute_total_temp(self):
        self.ensure_one()
        self.qty_planted_temp = 0
        for item in self.batchline_ids:
            self.qty_planted_temp += item.qty_planted
        return True


    # on change report after change stage
    @api.multi
    @api.onchange('reportline_id','selection_ids')
    def _change_report_stage(self):
        self.ensure_one()
        selection = self.env['estate.nursery.selection'].search([('stage_id', '=', 2),
                                                                   ('batch_id', '=', self.id)])
        if selection :
            self.reportline_id.id = 2
        self.write({'reportline_id' : self.reportline_id})

    #Set flag to show cleaving Seed
    @api.multi
    @api.onchange('selection_count','status')
    def _change_flag_selection(self):
        self.ensure_one()
        flag = self.selection_count
        if self.selection_count >= 4:
            self.status = True
        # return True

    @api.one
    @api.depends('age_seed_range','status_age','status','selection_count')
    def _change_flag_age(self):
        if self.age_seed_range >= 3 :
            self.status_age = True
            if self.status == True:
                self.status_age = False
        # return False

    #todo message notification to group user or user manager for every batch transfer to mn
    # @api.one
    # def send_message_notification(self):
    #     #for send message notification to group user or user manager for every batch transfer to mn.
    #     if self.age_seed_range > 3 or self.age_seed_range < 6:
    #         send_data = {
    #             'model': self.model,
    #             'subject': subject_rendered,
    #             'body': 'Please for send to Mn %s Because Seed age %s' %(self.lot_id.product_id.display_name,self.age_seed_range) ,
    #             }
    #
    #         sendnotif = self.env['message_template.mixin'].create(send_data)
    #         sendnotif.send()
    #         sendnotif.send_group()


    @api.multi
    @api.onchange('age_seed','age_seed_planted','date_planted')
    def _compute_age_planted(self):
        self.ensure_one()
        fmt = '%Y-%m-%d'
        today = datetime.now()
        if today:
            from_date = today
            to_date = self.date_planted
            conv_todate = datetime.strptime(str(to_date), fmt)
            d1 = from_date.month
            d2 = conv_todate.month
            rangeyear = conv_todate.year
            rangeyear1 = from_date.year
            rsult = rangeyear - rangeyear1
            yearresult = rsult * 12
            if today:
                if yearresult == 0 :
                    ageseed = (d2-d1)
                    self.age_seed_planted = ageseed + int(self.age_seed)
                elif yearresult > 0:
                    ageseed = (d2 + yearresult) - d1
                    self.age_seed_planted = ageseed + int(self.age_seed)

    #todo calculate age per month
    # @api.onchange('age_seed_range')
    # def _onchange_age_seed_range(self):
    #     #to change age per month
    #     fmt = '%Y-%m-%d'
    #     today = datetime.now()
    #     if self.date_received:
    #         from_date = self.date_received
    #         to_date = today
    #         conv_fromdate = datetime.strptime(str(from_date), fmt)
    #         d1 = to_date.month
    #         d2 = conv_fromdate.month
    #         rangeyear = conv_fromdate.year
    #         rangeyear1 = to_date.year
    #         rsult = rangeyear - rangeyear1
    #         yearresult = rsult * 12
    #         if yearresult == 0 :
    #                 ageseed = (d1-d2)
    #                 self.age_seed_range = ageseed + int(self.age_seed)
    #         elif yearresult > 0:
    #                 ageseed = (d1 + yearresult) - d2
    #                 self.age_seed_range = ageseed + int(self.age_seed)

    #computed age seed from cleaving,selection,recovery selection
    @api.multi
    @api.depends('month','selection_ids','cleaving_ids','recovery_ids','age_seed','date_planted','age_seed_range')
    def _compute_age_total(self):
        fmt = '%Y-%m-%d'
        today = datetime.now()
        if self.selection_ids or self.cleaving_ids or self.recovery_ids or self.date_planted:
            if self.date_planted :
                from_date = today
                to_date = self.date_planted
                conv_todate = datetime.strptime(str(to_date), fmt)
                d1 = from_date.month
                d2 = conv_todate.month
                rangeyear = conv_todate.year
                rangeyear1 = from_date.year
                rsult = rangeyear - rangeyear1
                yearresult = rsult * 12
                if yearresult == 0 :
                    ageseed = (d2-d1)
                    self.age_seed_range = ageseed + int(self.age_seed)
                elif yearresult > 0:
                    ageseed = (d2 + yearresult) - d1
                    self.age_seed_range = ageseed + int(self.age_seed)
            if self.selection_ids:
                for date in self.selection_ids:
                    date_selection = date.selection_date
                from_date = self.date_planted
                conv_fromdate = datetime.strptime(str(from_date), fmt)
                conv_todate = datetime.strptime(str(date_selection), fmt)
                date_conv_tomonth = conv_todate.month
                date_conv_frommonth = conv_fromdate.month
                rangeyear = conv_todate.year
                rangeyear1 = conv_fromdate.year
                rsult = rangeyear - rangeyear1
                yearresult = rsult * 12
                if yearresult == 0 :
                    month=date_conv_tomonth-date_conv_frommonth
                    self.age_seed_range = month
                elif yearresult > 0:
                    month= (date_conv_tomonth+yearresult)-date_conv_frommonth
                    monthtemp = self.age_seed_range +month
                    self.age_seed_range = monthtemp
            if self.cleaving_ids:
                for date in self.cleaving_ids:
                    date_cleaving = date.cleaving_date
                from_date = self.date_planted
                conv_fromdate = datetime.strptime(str(from_date), fmt)
                conv_todate = datetime.strptime(str(date_cleaving), fmt)
                date_conv_tomonth = conv_todate.month
                date_conv_frommonth = conv_fromdate.month
                rangeyear = conv_todate.year
                rangeyear1 = conv_fromdate.year
                rsult = rangeyear - rangeyear1
                yearresult = rsult * 12
                if yearresult == 0 :
                    month=date_conv_tomonth-date_conv_frommonth
                    self.age_seed_range = month
                elif yearresult > 0:
                    month= (date_conv_tomonth+yearresult)-date_conv_frommonth
                    monthtemp = self.age_seed_range +month
                    self.age_seed_range = monthtemp
            if self.recovery_ids:
                for date in self.recovery_ids:
                    date_recovery = date.recovery_date
                from_date = self.date_planted
                conv_fromdate = datetime.strptime(str(from_date), fmt)
                conv_todate = datetime.strptime(str(date_recovery), fmt)
                date_conv_tomonth = conv_todate.month
                date_conv_frommonth = conv_fromdate.month
                rangeyear = conv_todate.year
                rangeyear1 = conv_fromdate.year
                rsult = rangeyear - rangeyear1
                yearresult = rsult * 12
                if yearresult == 0 :
                    month=date_conv_tomonth-date_conv_frommonth
                    self.age_seed_range = month
                elif yearresult > 0:
                    month= (date_conv_tomonth+yearresult)-date_conv_frommonth
                    monthtemp = self.age_seed_range +month
                    self.age_seed_range = monthtemp



class Batchline(models.Model):
    """Batch Line to record seed selection and planting by box/bag."""
    _name = 'estate.nursery.batchline'
    _description = "Seed Batch Line (Box/Bag)"
    _parent_store = True
    _parent_name = "parent_id"
    _parent_order = "name"

    name = fields.Char("Name")
    complete_name = fields.Char("Supplier Packaging ID")
    packaging_id = fields.Many2one('product.packaging', "Packaging Type")
    parent_id = fields.Many2one('estate.nursery.batchline', "Parent Package", ondelete="restrict")
    parent_left = fields.Integer('Parent Left', index=True)
    parent_right = fields.Integer('Parent Right', index=True)
    child_ids = fields.One2many('estate.nursery.batchline', 'parent_id', "Contains")
    batch_id = fields.Many2one('estate.nursery.batch', "Batch", ondelete="restrict")
    total_qty_parent=fields.Integer("DO Quantity")
    seed_qty = fields.Integer("DO Quantity")
    qty_single = fields.Integer("Single Tone Quantity",store=True)
    qty_double = fields.Integer("Double Tone Quantity",store=True)
    qty_broken = fields.Integer("Broken Seed Quantity",store=True)
    qty_dead = fields.Integer("Dead Seed Quantity",store=True)
    qty_fungus = fields.Integer("Fungus Seed Quantity",store=True)
    subtotal_normal = fields.Integer("Normal Seed Quantity", compute='_compute_subtotal',store=True)
    subtotal_abnormal = fields.Integer("Abnormal Seed Quantity", compute='_compute_subtotal',store=True)
    percentage_normal = fields.Float("Normal Ratio", digits=(2,2), compute='_compute_subtotal',store=True)
    percentage_abnormal = fields.Float("Abnormal Ratio", digits=(2,2), compute='_compute_subtotal',store=True)
    selection_do_var = fields.Integer("Variance", help="Seed selection ratio.", compute='_compute_variance')
    planting_selection_var = fields.Integer("Variance", help="Seed planted ratio", compute='_compute_variance')
    qty_planted = fields.Integer("Planted Quantity",store=True)
    location_id = fields.Many2one('estate.block.template', "Bedengan/Plot",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '3'),
                                          ('estate_location_type', '=', 'nursery'),
                                          ('stage_id','=',1),
                                          ('scrap_location', '=', False)],
                                  help="Fill in location seed planted.")
    flag_bag= fields.Boolean('Bag or box ?')

    @api.one
    @api.depends('qty_single', 'qty_double', 'qty_broken', 'qty_dead', 'qty_fungus')
    def _compute_subtotal(self):
        # self.ensure_one()
        """Compute number and percentage of subtotal"""

        self.subtotal_normal = self.qty_single + self.qty_double
        self.subtotal_abnormal = self.qty_broken + self.qty_dead + self.qty_fungus
        total = self.subtotal_normal + self.subtotal_abnormal

        # self.ensure_one()
        # Prevent division by zero as selection did not happen yet
        if total:
            self.percentage_normal = float(self.subtotal_normal) / float(total) * 100.00
            self.percentage_abnormal = float(self.subtotal_abnormal) / float(total) * 100.00

    @api.one
    @api.depends('subtotal_normal', 'subtotal_abnormal', 'qty_planted')
    def _compute_variance(self):
        # self.ensure_one()
        """Compute variance of received and planted."""

        if self.qty_single and self.qty_double and self.qty_broken and self.qty_dead and self.qty_fungus:
            self.selection_do_var = (self.subtotal_normal + self.subtotal_abnormal) - self.seed_qty
            self.planting_selection_var = self.qty_planted - self.subtotal_normal


class Box(models.Model):
    """Deprecated. Use Batchline."""
    _name = 'estate.nursery.box'

    name = fields.Char("Box Number")
    batch_id = fields.Many2one('estate.nursery.batch', "Box Number")
    condition_id = fields.Many2one('estate.nursery.condition', "Box Condition", domain="[('condition_category','=','1')]")
    bag_ids = fields.One2many('estate.nursery.bag', 'box_id', "Bags/Plastics")

class Bag(models.Model):
    """Deprecated. Use Batchline."""
    _name = 'estate.nursery.bag'

    name = fields.Char("Bag Number")
    box_id = fields.Many2one('estate.nursery.batch', "Box Number")
    condition_id = fields.Many2one('estate.nursery.condition', "Bag/Plastic Condition", domain="[('condition_category','=','1')]")
    qty_seed = fields.Integer("Seed Quantity")


class SeedPackaging(models.Model):

    _name = 'product.ul'
    _description = "Logistic Unit"

    name= fields.Char('Name', select=True, required=True, translate=True)
    type= fields.Selection([('unit','Unit'),('pack','Pack'),('box', 'Box'), ('pallet', 'Pallet')], 'Type', required=True)
    height= fields.Float('Height', help='The height of the package')
    width= fields.Float('Width', help='The width of the package')
    length= fields.Float('Length', help='The length of the package')
    weight= fields.Float('Empty Package Weight')

class InheritProductPackaging(models.Model):

    _inherit = 'product.packaging'

    ul = fields.Many2one('product.ul', 'Package Logistic Unit', required=True)
    ul_qty = fields.Integer('Package by layer', help='The number of packages by layer')
    ul_container = fields.Many2one('product.ul', 'Pallet Logistic Unit')
    ean=fields.Char('EAN', size=14, help="The EAN code of the package unit.")
    rows= fields.Integer('Number of Layers', required=True,
            help='The number of layers on a pallet or box')
    code= fields.Char('Code', help="The code of the transport unit.")
    weight= fields.Float('Total Package Weight',
            help='The weight of a full package, pallet or box.')

    def _check_ean_key(self, cr, uid, ids, context=None):
        for pack in self.browse(cr, uid, ids, context=context):
            if not check_ean(pack.ean):
                return False
        return True

    _constraints = [(_check_ean_key, 'Error: Invalid ean code', ['ean'])]

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        res = []
        for pckg in self.browse(cr, uid, ids, context=context):
            p_name = pckg.ean and '[' + pckg.ean + '] ' or ''
            p_name += pckg.ul.name
            res.append((pckg.id,p_name))
        return res

    def _get_1st_ul(self, cr, uid, context=None):
        cr.execute('select id from product_ul order by id asc limit 1')
        res = cr.fetchone()
        return (res and res[0]) or False

    _defaults = {
        'rows' : 3,
        'sequence' : 1,
        'ul' : _get_1st_ul,
    }

    def checksum(ean):
        salt = '31' * 6 + '3'
        sum = 0
        for ean_part, salt_part in zip(ean, salt):
            sum += int(ean_part) * int(salt_part)
        return (10 - (sum % 10)) % 10
    checksum = staticmethod(checksum)

class StockPicking(models.Model):

    _inherit = 'stock.picking'

    age_seed = fields.Integer("Seed Age")

    @api.multi
    def do_new_transfer(self):
        """
        Extend stock transfer wizard to create stock move and lot.
        """
        #check if this stock_picking is not from nursery
        if not self.age_seed or self.age_seed <= 0:
            super(StockPicking, self).do_new_transfer()
            return True
        
        self.ensure_one()
        date_done = self.min_date
        arrQtyDone = []
        arrQtyProduct = []
        # Iterate through transfer detail item
        for item in self.pack_operation_product_ids:
            if item.product_id.seed:
                if date_done or item.variety_id:
                    lot_new = self.do_create_lot(item.product_id)
                    item.write({'lot_id': lot_new[0].id})
                    batch = self.do_create_batch(item, self, lot_new[0])
                    self.do_create_batchline(item, batch[0])
                if self.env['stock.picking'].search([('state','=','assigned')]):
                    packaging = self.env['stock.pack.operation'].search([('picking_id.id','=',self.id)])
                    for quantity in packaging:
                        arrQtyDone.append(quantity.qty_done)
                        arrQtyProduct.append(quantity.product_qty)
                    if arrQtyDone < arrQtyProduct:
                        error_msg = "Quantity Done can not be lower than Quantity Product "
                        raise exceptions.ValidationError(error_msg)
                    elif arrQtyDone > arrQtyProduct:
                        error_msg = "Quantity Done can not be greater than Quantity Product "
                        raise exceptions.ValidationError(error_msg)
                else:
                    raise exceptions.Warning('Required Date of Transfer and Variety')
            super(StockPicking, self).do_new_transfer()

        return True


    @api.multi
    def do_create_lot(self, product):
        serial = self.env['estate.nursery.batch'].search_count([]) + 1

        self.ensure_one()

        lot_data = {
            'name': "Batch %d" % serial,
            'product_id': product.id
        }

        return self.env['stock.production.lot'].create(lot_data)

    @api.multi
    def do_create_batch(self, item, transfer, lot):
        """Create Lot and Seed Batch per transfer item."""

        self.ensure_one()
        date_done = transfer.min_date
        # partner = transfer.picking_id.partner_id
        # product = item.product_id

        serial = self.env['estate.nursery.batch'].search_count([]) + 1

        # Validate Picking Date of Transfer
        if not date_done:
            raise exceptions.Warning('Press Cancel button and fill in date of transfer at Additional Info Tab.')

        batch_data = {
            'name': "Batch %d" % serial,
            'lot_id': lot.id,
            'variety_id': item.variety_id.id,
            'date_received': date_done,
            'age_seed': transfer.age_seed,
            'qty_received': item.product_qty,
            'picking_id': transfer.id,
            'state': 'draft'
        }

        return self.env['estate.nursery.batch'].create(batch_data)

    @api.multi
    def do_create_batchline(self, item, batch):
        """Calculate and create seed bag. Default if no packaging found is 100 seed/bag."""
        product = item.product_id

        self.ensure_one()

        if len(product.packaging_ids) > 0:
            pak = product.packaging_ids[0] # Always get first packaging
            pak_row = pak.rows
            pak_row_bag = pak.ul_qty
            pak_total_bag = pak.rows * pak.ul_qty
            pak_bag_content = pak.qty
            pak_box_content = pak.qty * pak_total_bag #content box full

        else:
            raise exceptions.Warning('Product %s has no packaging. Contact Administrator.' % product.name)

        pak_content = pak_row * pak_row_bag * pak_bag_content

        item_qty = item.product_qty
        serial = 0

        # todo recode using recursive call (http://goo.gl/rjRtEs)

        # Count full box
        box_amount_full = int(item_qty/pak_content)
        pak_box_half_content = (item_qty % pak_content)

        if item_qty % pak_content:
            box_amount_half = 1
        else:
            box_amount_half = 0

        total_box = box_amount_full + box_amount_half
        print total_box

        if box_amount_full:
            for i in range(box_amount_full):
                serial += 1
                bag_serial = 0
                box_data = {
                    'name': "%s / Box %d" % (batch.name, serial),
                    'batch_id': batch.id,
                    'packaging_id': pak.id,
                    'total_qty_parent' : pak_box_content
                }
                box = self.env['estate.nursery.batchline'].create(box_data)

                for d in range(pak_total_bag):
                    bag_serial += 1
                    bag_data = {
                        'name': "%s / Bag %d.%d" % (box.name, serial, bag_serial),
                        'batch_id': batch.id,
                        'packaging_id': pak.id,
                        'parent_id': box.id,
                        'seed_qty': pak_bag_content,
                        'flag_bag' : 1
                    }
                    self.env['estate.nursery.batchline'].create(bag_data)

        if box_amount_half:
            print "Create 1 half box (amount %d seed)" % (item_qty % pak_content)
            serial += 1
            bag_serial = 0
            seed_qty = item_qty % pak_content
            bag_amount_full = int(seed_qty/pak_bag_content)
            box_data = {
                'name': "%s / Box %d" % (batch.name, serial),
                'batch_id': batch.id,
                'packaging_id': pak.id,
                'total_qty_parent' : pak_box_half_content
            }
            box = self.env['estate.nursery.batchline'].create(box_data)

            if bag_amount_full:
                print "  Create %d full bag" % bag_amount_full
                for i in range(bag_amount_full):
                    bag_serial += 1
                    bag_data = {
                        'name': "%s / Bag %d.%d" % (box.name, serial, bag_serial),
                        'batch_id': batch.id,
                        'packaging_id': pak.id,
                        'parent_id': box.id,
                        'seed_qty': pak_bag_content,
                        'flag_bag' : 1
                    }
                    self.env['estate.nursery.batchline'].create(bag_data)

            if seed_qty % pak_bag_content:
                bag_amount_half = 1
                bag_serial += 1
                bag_data = {
                    'name': "%s / Bag %d.%d" % (box.name, serial, bag_serial),
                    'batch_id': batch.id,
                    'packaging_id': pak.id,
                    'parent_id': box.id,
                    'seed_qty': seed_qty % pak_bag_content,
                    'flag_bag' : 1
                }
                self.env['estate.nursery.batchline'].create(bag_data)

        return True


class StockPackOperation(models.Model):

    _inherit ='stock.pack.operation'

    is_seed = fields.Boolean("Is Seed", related='product_id.seed')
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety",
                                 ondelete="restrict",related='product_id.variety_id')

#-----------------------------------------------------------------------------------------------------------------#
#Different in odoo 8 and odoo 9, odoo 9 not have a stock transfer detail, because the version ot clear for packaging.
# and in odoo 9 not use stock_transfer detail, look at down this code for nursery inherit stock transfer detail ini odoo 8

# class TransferDetail(models.TransientModel):
#     """Extend Transfer Detail to create Seed Batch."""
#     _inherit = 'stock.transfer_details'
#
#     age_seed = fields.Integer("Seed Age")
#
#
#     @api.one
#     def do_detailed_transfer(self):
#         """
#         Extend stock transfer wizard to create stock move and lot.
#         """
#         date_done = self.picking_id.date_done
#
#         # Iterate through transfer detail item
#         for item in self.item_ids:
#             if item.product_id.seed:
#                 if date_done or item.variety_id:
#                     lot_new = self.do_create_lot(item.product_id)
#                     item.write({'lot_id': lot_new[0].id})
#                     batch = self.do_create_batch(item, self, lot_new[0])
#                     self.do_create_batchline(item, batch[0])
#                 else:
#                     raise exceptions.Warning('Required Date of Transfer and Variety')
#             super(TransferDetail, self).do_detailed_transfer()
#
#         return True
#
#     @api.one
#     def do_create_lot(self, product):
#         serial = self.env['estate.nursery.batch'].search_count([]) + 1
#
#         lot_data = {
#             'name': "Batch %d" % serial,
#             'product_id': product.id
#         }
#
#         return self.env['stock.production.lot'].create(lot_data)
#
#     @api.one
#     def do_create_batch(self, item, transfer, lot):
#         """Create Lot and Seed Batch per transfer item."""
#         date_done = transfer.picking_id.date_done
#         # partner = transfer.picking_id.partner_id
#         # product = item.product_id
#
#         serial = self.env['estate.nursery.batch'].search_count([]) + 1
#
#         # Validate Picking Date of Transfer
#         if not date_done:
#             raise exceptions.Warning('Press Cancel button and fill in date of transfer at Additional Info Tab.')
#
#         batch_data = {
#             'name': "Batch %d" % serial,
#             'lot_id': lot.id,
#             'variety_id': item.variety_id.id,
#             'date_received': date_done,
#             'age_seed': transfer.age_seed,
#             'qty_received': item.quantity,
#             'picking_id': transfer.picking_id.id,
#             'state': 'draft'
#         }
#
#         # print "Create Seed Batch. %s (v: %s, p: %s) is received at %s from %s" % (item.product_id.name,
#         #                                                                                 item.variety_id.name,
#         #                                                                                 item.progeny_id.name,
#         #                                                                                 date_done,
#         #                                                                                 partner.name)
#
#         # Check and create batch (box) and batchline (bag) for seed product.
#         #       if product has no package
#         #           create one box and one bag
#         #       else
#         #           create batch and its batchline as product package.
#         # Check and create lot for current good receipt
#         # print "Create Box and Bag Packaging is %s (box: %s, bag: %s @ %s)" % (product.name,
#         #                                                    packaging.ul_container.name,
#         #                                                    packaging.ul.name,
#         #                                                    packaging.qty * packaging.ul_qty)
#
#         return self.env['estate.nursery.batch'].create(batch_data)
#
#     @api.one
#     def do_create_batchline(self, item, batch):
#         """Calculate and create seed bag. Default if no packaging found is 100 seed/bag."""
#         product = item.product_id
#
#         print 'Packaging %d' % len(product.packaging_ids)
#
#         if len(product.packaging_ids) > 0:
#             pak = product.packaging_ids[0] # Always get first packaging
#             pak_row = pak.rows
#             pak_row_bag = pak.ul_qty
#             pak_total_bag = pak.rows * pak.ul_qty
#             pak_bag_content = pak.qty
#             pak_box_content = pak.qty * pak_total_bag #content box full
#
#         else:
#             raise exceptions.Warning('Product %s has no packaging. Contact Administrator.' % product.name)
#
#         pak_content = pak_row * pak_row_bag * pak_bag_content
#
#         item_qty = item.quantity
#         serial = 0
#
#         # todo recode using recursive call (http://goo.gl/rjRtEs)
#
#         # Count full box
#         box_amount_full = int(item_qty/pak_content)
#         pak_box_half_content = (item_qty % pak_content)
#
#         if item_qty % pak_content:
#             box_amount_half = 1
#         else:
#             box_amount_half = 0
#
#         total_box = box_amount_full + box_amount_half
#         print total_box
#
#         if box_amount_full:
#             for i in range(box_amount_full):
#                 serial += 1
#                 bag_serial = 0
#                 box_data = {
#                     'name': "%s / Box %d" % (batch.name, serial),
#                     'batch_id': batch.id,
#                     'packaging_id': pak.id,
#                     'total_qty_parent' : pak_box_content
#                 }
#                 box = self.env['estate.nursery.batchline'].create(box_data)
#
#                 for d in range(pak_total_bag):
#                     bag_serial += 1
#                     bag_data = {
#                         'name': "%s / Bag %d.%d" % (box.name, serial, bag_serial),
#                         'batch_id': batch.id,
#                         'packaging_id': pak.id,
#                         'parent_id': box.id,
#                         'seed_qty': pak_bag_content,
#                         'flag_bag' : 1
#                     }
#                     self.env['estate.nursery.batchline'].create(bag_data)
#
#         if box_amount_half:
#             print "Create 1 half box (amount %d seed)" % (item_qty % pak_content)
#             serial += 1
#             bag_serial = 0
#             seed_qty = item_qty % pak_content
#             bag_amount_full = int(seed_qty/pak_bag_content)
#             box_data = {
#                 'name': "%s / Box %d" % (batch.name, serial),
#                 'batch_id': batch.id,
#                 'packaging_id': pak.id,
#                 'total_qty_parent' : pak_box_half_content
#             }
#             box = self.env['estate.nursery.batchline'].create(box_data)
#
#             if bag_amount_full:
#                 print "  Create %d full bag" % bag_amount_full
#                 for i in range(bag_amount_full):
#                     bag_serial += 1
#                     bag_data = {
#                         'name': "%s / Bag %d.%d" % (box.name, serial, bag_serial),
#                         'batch_id': batch.id,
#                         'packaging_id': pak.id,
#                         'parent_id': box.id,
#                         'seed_qty': pak_bag_content,
#                         'flag_bag' : 1
#                     }
#                     self.env['estate.nursery.batchline'].create(bag_data)
#
#             if seed_qty % pak_bag_content:
#                 bag_amount_half = 1
#                 bag_serial += 1
#                 bag_data = {
#                     'name': "%s / Bag %d.%d" % (box.name, serial, bag_serial),
#                     'batch_id': batch.id,
#                     'packaging_id': pak.id,
#                     'parent_id': box.id,
#                     'seed_qty': seed_qty % pak_bag_content,
#                     'flag_bag' : 1
#                 }
#                 self.env['estate.nursery.batchline'].create(bag_data)
#
#         return True
#
# class TransferDetailItem(models.TransientModel):
#     """
#     Extend Transfer Detail Items to include Variety and Progeny information
#     """
#     _inherit = 'stock.transfer_details_items'
#
#     is_seed = fields.Boolean("Is Seed", related='product_id.seed')
#     variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety",
#                                  ondelete="restrict",related='product_id.variety_id')

# class InheritEstateBlockTemplate(models.Model):
#
#     _inherit='estate.block.template'
#
#     batch_id = fields.Many2one('estate.nursery.batch','Seed Source',required=False,ondelete="restrict",
#                                help='use batch for nursery block only.')

