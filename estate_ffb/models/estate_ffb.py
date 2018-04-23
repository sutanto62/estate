# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import models, fields, api, exceptions, _
from openerp.exceptions import ValidationError

import openerp.addons.decimal_precision as dp

RESET_PERIOD = [('year', 'Every Year'), ('month', 'Every Month')]
RESET_PERIOD_TIMEDELTA = [('year', 12), ('month', 1)]

class EstateFFB(models.Model):
    
    _name = 'estate.ffb'
    _description = 'Fresh Fruit Bunches'
    _inherit=['mail.thread']
    
    name = fields.Char("Name", required=True, store=True, default='New')
    date = fields.Date("Date", default=fields.Date.context_today, required=True)
    max_day = fields.Integer("Date Constraint", help='Change to override maximum harvest date day(s) configuration')
    clerk_id = fields.Many2one('hr.employee', string="Clerk", required=True)  # constrains: if team_id.assistant_id = true
    team_ids = fields.Many2many('estate.hr.team', string="Team", required=True)
    team_member_ids = fields.One2many('estate.hr.member',  
                                      domain="[('team_id', 'in', team_ids)]", store=False)
    estate_id = fields.Many2one('stock.location', "Estate",
                                domain=[('estate_location', '=', True), ('estate_location_level', '=', '1'),
                                ('estate_location_type', '=', 'planted')],required=True)
    company_id = fields.Many2one('res.company', 'Company', help='Define location company.', required=True)
    division_id = fields.Many2one('stock.location', "Division", required=True,
                                  domain=[('estate_location', '=', True), ('estate_location_level', 'in', ['1','2'])])
    approver_id = fields.Many2one('hr.employee', "Agronomy Assistant", required=True)  # constrains: if team_id.assistant_id = true
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('approved', 'Approved'),
                              ('rejected', 'Rejected')], "State", default="draft", track_visibility="onchange")
    validation_confirm = fields.Boolean("Validation Requester",compute='_compute_validation_confirm', store=False)
    description = fields.Text("Description")
    ffb_detail_ids = fields.One2many('estate.ffb.detail', string='FFB Line', inverse_name='ffb_id')

    @api.multi
    def _compute_validation_confirm(self):
        """ check validation user create_uid to confirm. """
        for rec in self:
            rec.validation_confirm = False
            if rec.create_uid.id == self.get_user().id:
                rec.validation_confirm = True

    @api.one
    @api.constrains('date')
    def _check_date(self):
        """Harvest date should be limited. Didn't support different timezone
        Condition:
        1. Zero value of max entry day = today transaction should be entry today.
        2. Positive value of max entry day = allowed back/future dated transaction.
        """
        if self.date:
            fmt = '%Y-%m-%d'
            d1 = datetime.strptime(self.date, fmt)
            d2 = datetime.strptime(fields.Date.today(), fmt)
            delta = (d2 - d1).days
            if self.max_day == 0 and abs(delta) > self.max_day:
                error_msg = _("Transaction date should be today")
                raise ValidationError(error_msg)
            elif self.max_day != 0 and abs(delta) > self.max_day:
                error_msg = _(
                    "Transaction date should not be less than/greater than or equal to %s day(s)" % self.max_day)
                raise ValidationError(error_msg)
            else:
                return True

    @api.constrains('clerk_id')
    def _check_clerk_id(self):
        """
        Check each Bunch Count Sheet with current date is for single clerk_id.
        """
        ffb_ids = self.search([('date', '=', self.date), ('clerk_id', '=', self.clerk_id.id)]).ids

        if len(ffb_ids) > 1:
            error_msg = _("Bunch Count Sheet with current Clerk is already created today.")
            raise ValidationError(error_msg)

    @api.model
    def create(self, vals):
        """ Get sequence for ffb"""
        if vals.get('name', 'New') == 'New':
            seq_obj = self.env['ir.sequence']
            estate_name = self.env['stock.location'].search([('id', '=', vals['estate_id'])])

            vals['name'] = seq_obj.with_context(ir_sequence_code_1=estate_name.name,
                                                ir_sequence_date=vals['date']).next_by_code('estate.ffb') or '/'

        return super(EstateFFB, self).create(vals)

    @api.multi
    def action_draft(self):
        self.state='draft'

    @api.multi
    def action_confirm(self):
        self.state='confirmed'

    @api.multi
    def action_approve(self):
        self.state='approved'

    @api.multi
    def action_reject(self):
        self.state='rejected'

    @api.multi
    def get_user(self):
        for rec in self:
            user = rec.env['res.users'].browse(rec.env.uid)
            return user

    
class EstateFFBDetail(models.Model):
    
    _name = 'estate.ffb.detail'
    _description = 'Fresh Fruit Bunches Detail'
    _inherit=['mail.thread']
    
    ffb_id = fields.Many2one('estate.ffb', string='FFB', ondelete='cascade')
    upkeep_date = fields.Date(related='ffb_id.date', string='Date', store=True)
    employee_id = fields.Many2one('hr.employee', 'Harvester', required=True, track_visibility='onchange',
                                  domain=[('contract_type', 'in', ['1', '2'])])
    employee_nik = fields.Char(related='employee_id.nik_number', string="Employee Identity Number ", store=True)
    employee_company_id = fields.Many2one(related='employee_id.company_id', string='Employee Company', store=True,
                                          help="Company of employee")
    team_id = fields.Many2one('estate.hr.team', string="Team")
    division_id = fields.Many2one(related='ffb_id.division_id', string='Division',
                            help='Define division of employee.', compute="_compute_division")
    tph_id = fields.Many2one('estate.block.template', 'TPH',
                                  domain="[('inherit_location_id.location_id.location_id.location_id', '=', division_id)]")
    block_id = fields.Many2one(related='tph_id.inherit_location_id.location_id.location_id', string='Block', store=True,
                            help='Define block of tph.')
    location_id = fields.Many2one('estate.block.template', 'Location', store=True)
    planted_year_id = fields.Many2one(related='location_id.planted_year_id', 
                                      string='Planted Year', store=True)
    qty_n = fields.Float('Ripe (N)', track_visibility='onchange',
                                       help='Define ripe ffb', digits=(4,0))
    qty_a = fields.Float('Unripe (A)', track_visibility='onchange',
                                       help='Define unripe ffb', digits=(4,0))
    qty_e = fields.Float('Overripe (E)', track_visibility='onchange',
                                       help='Define overripe ffb', digits=(4,0))
    qty_l = fields.Float('Long Stalk (L)', track_visibility='onchange',
                                       help='Define long stalk ffb', digits=(4,0))
    qty_b = fields.Float('Loose Fruit (B)', track_visibility='onchange',
                                       help='Define loose ffb', digits=(4,0))
    flag_s = fields.Boolean('Not Stacked (S)', track_visibility='onchange',
                                       help='Define not stacked status ffb')
    flag_k = fields.Boolean('Not on Sack (K)', track_visibility='onchange',
                                       help='Define not on sack status ffb')
    
    @api.one
    def _compute_division(self):
        """Define location domain while editing record
        """
        self.division_id = self.ffb_id.division_id
        
    @api.onchange('tph_id')
    def _onchange_tph_id(self):
        """Define location domain while editing record
        """
        block = self.env['estate.block.template'].search([('inherit_location_id', '=', self.tph_id.inherit_location_id.location_id.location_id.id)])
        if len(block):
            self.location_id = block[0]

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """
        Define harvesting employee based on selected team_ids.
        """
        team_ids = self.ffb_id.team_ids.ids
        if team_ids:
            """ Filter employee based on selected team """
            current_worker = []
            hr_member_ids = self.env['estate.hr.member'].search([('team_id', 'in', team_ids)])
            for member in hr_member_ids:
                current_worker.append(member.employee_id.id)

            """ Get team_id of this employee_id"""
            member_id = self.env['estate.hr.member'].search([('team_id', 'in', team_ids),
                                                             ('employee_id', '=', self.employee_id.id)])
            self.team_id = member_id.team_id.id

            return {
                'domain': {
                    'employee_id': [('id', 'in', current_worker)]
                }
            }
