# -*- coding: utf-8 -*-
from datetime import datetime

from openerp import models, fields, api, exceptions, _
from openerp.exceptions import ValidationError

class EstatePayrolFFB(models.Model):
    """
    Team activity records. It record harvest labour activity.
    """
    _name = 'estate.payrollffb'
    _description = 'Payroll FFB'
    _inherit=['mail.thread']
    
    def get_date_number(self, str_date):
        date_date = datetime.strptime(str_date, '%Y-%m-%d')
        return date_date.weekday()
    
    def get_is_holiday(self, str_date):
        #implementation of is holiday day, currently is for sunday 6
        #should be able to get public holiday too
        return self.get_date_number(self.date) == 6
    
    def get_is_friday(self, str_date):
        return self.get_date_number(self.date) == 4
    
    name = fields.Char("Name", required=True, store=True, default='New')
    date = fields.Date("Date", default=fields.Date.context_today, required=True)
    max_day = fields.Integer("Date Constraint", help='Change to override maximum harvest date day(s) configuration')
    date_number = fields.Integer("Date Number", compute='_compute_date', store=False)
    is_friday = fields.Boolean("Friday", compute='_compute_is_friday', store=False)
    is_holiday = fields.Boolean("Holiday", compute='_compute_is_holiday', store=False)
    team_id = fields.Many2one('estate.hr.team', "Team", required=True)
    team_member_ids = fields.One2many(related='team_id.member_ids', string='Member', store=False)
    estate_id = fields.Many2one('stock.location', "Estate",
                                domain=[('estate_location', '=', True), ('estate_location_level', '=', '1'),
                                ('estate_location_type', '=', 'planted')],required=True)
    company_id = fields.Many2one('res.company', 'Company', help='Define location company.', required=True)
    division_id = fields.Many2one('stock.location', "Division", required=True,
                                  domain=[('estate_location', '=', True), ('estate_location_level', 'in', ['1','2'])])
    approver_id = fields.Many2one('hr.employee', "Approver")  # constrains: if team_id.assistant_id = true
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('agr_asst_approved', 'Agronomy Assistant Approved'),
                              ('agr_head_approved', 'Agronomy Head Assistant Approved'),
                              ('estate_mgr_approved', 'Estate Manager Approved'),
                              ('approved', 'Full Approved'),
                              ('rejected', 'Rejected')], "State", default="draft", track_visibility="onchange")
    description = fields.Text("Description")
    labour_line_ids = fields.One2many('estate.payrollffb.labour', string='Harvest Labour', inverse_name='payrollffb_id')
    
    def _compute_date(self):
        self.date_number = self.get_date_number(self.date)
    
    def _compute_is_friday(self):
        self.is_friday = self.get_is_friday(self.date)
    
    def _compute_is_holiday(self):
        self.is_holiday = self.get_is_holiday(self.date)

    @api.constrains('date')
    def _check_date(self):
        """
        Harvest Labour date should be limited. Didn't support different timezone
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
                error_msg = _("Transaction date should not be less than/greater than or equal to %s day(s)" % self.max_day)
                raise ValidationError(error_msg)
            else:
                return True

    @api.constrains('team_id')
    def _check_team_id(self):
        """ Check each employee in estate.payrollffb.details is the correct team member.
        Check each LHMP with current date is for single team_id. """
        self.check_employee_membership()
        self.check_team_id_daily_payrollffb()

        return True

    @api.constrains('labour_line_ids')
    def _check_labour_line_ids_team_id(self):
        """ Check each employee in estate.payrollffb.details is the correct team member. """
        self.check_employee_membership()
        self.check_attendance_code_id()
        return True

    @api.model
    def create(self, vals):
        """ Get sequence number for estate.payrollffb"""
        if vals.get('name', 'New') == 'New':
            seq_obj = self.env['ir.sequence']
            estate_name = self.env['stock.location'].search([('id', '=', vals['estate_id'])])

            vals['name'] = seq_obj.with_context(ir_sequence_code_1=estate_name.name,
                                                ir_sequende_date=vals['date']).next_by_code('estate.payrollffb') or '/'

        return super(EstatePayrolFFB, self).create(vals)

    def check_employee_membership(self):
        """ Check sum of employee in selected team vs employee on harvest labour details """

        if self.labour_line_ids:
            employee_ids = []
            for record in self.labour_line_ids:
                employee_ids.append(record.employee_id.id)

            hr_member_ids = self.env['estate.hr.member'].search([('employee_id', 'in', employee_ids),
                                                                 ('team_id', '=', self.team_id.id)])
            member_ids = map(lambda i: i.employee_id.id, hr_member_ids)

            if not set(employee_ids) == set(member_ids):
                error_msg = _("Each employee should be the member of the selected team.")
                raise ValidationError(error_msg)

        return True

    def check_team_id_daily_payrollffb(self):
        """ Check each Daily Harvest Labour Sheet for each team per days """
        payrollffb_ids = self.search([('date', '=', self.date), ('team_id', '=', self.team_id.id)]).ids

        if len(payrollffb_ids) > 1:
            error_msg = _("Daily Payroll FFB Labour Sheet with current Team is already created today.")
            raise ValidationError(error_msg)

        return True

    def check_attendance_code_id(self):
        """ Check attendance code. Max attendace is 1 workdays """
        if self.labour_line_ids:
            for rec in self.labour_line_ids:
                total_ratio_day = sum(a.attendance_code_id.qty_ratio for a in self.labour_line_ids
                                      if a.employee_id.id == rec.employee_id.id)

                if total_ratio_day > 1:
                    error_msg = _("Total worked day of %s should not more than 1 worked day" % rec.employee_id.name_related)
                    raise ValidationError(error_msg)
                    break

class EstatePayrollffbLabour(models.Model):
    
    _name = 'estate.payrollffb.labour'
    _description = 'Payroll FFB Labour'
    _inherit=['mail.thread']
    
    payrollffb_id = fields.Many2one('estate.payrollffb', string='Payroll FFB Labour', ondelete='cascade')
    date = fields.Date(related='payrollffb_id.date', string='Date', store=True)
    employee_id = fields.Many2one('hr.employee', 'Harvester', required=True, track_visibility='onchange',
                                  domain=[('contract_type', 'in', ['1', '2'])])
    employee_nik = fields.Char(related='employee_id.nik_number', string="Employee Identity Number ", store=True)
    employee_company_id = fields.Many2one(related='employee_id.company_id', string='Employee Company', store=True,
                                          help="Company of employee")
    division_id = fields.Many2one(related='location_id.inherit_location_id', string='Division',
                            help='Define division of employee.')
    attendance_code_id = fields.Many2one('estate.hr.attendance', 'Attendance', track_visibility='onchange',
                                    help='Any update will reset employee\'s timesheet')
    attendance_code_ratio = fields.Float('Ratio', digits=(4,2), related='attendance_code_id.qty_ratio')
    location_id = fields.Many2one('estate.block.template', 'Location', store=True)
    planted_year_id = fields.Many2one(related='location_id.planted_year_id', 
                                      string='Planted Year', store=True)
    qty_ffb = fields.Float('Qty FFB', track_visibility='onchange',
                                       help='Define quantity FFB', digits=(4,0))
    qty_loose_ffb = fields.Float('Qty Loose FFB', track_visibility='onchange',
                                       help='Define quantity loose FFB', digits=(4,0))
    qty_penalty = fields.Float('Penalty', track_visibility='onchange',
                                       help='Define penalty', digits=(4,0))
    cross_team = fields.Boolean('Cross Team Activity', default=False,
                                help='Cross Team (CT). Check to open all locations.')

    @api.onchange('location_id','cross_team')
    def _onchange_location_id(self):
        """ Change block selection based on cross_team flag value"""
        if not self.cross_team or self.cross_team == None:
            stock_location_ids = self.env['stock.location'].search([
                                                            ('location_id', '=', self.payrollffb_id.division_id.id)]).ids
            return {
                'domain': {
                    'location_id': [('inherit_location_id', 'in', stock_location_ids)]
                }
            }

        else:
            stock_location_ids = self.env['stock.location'].search([]).ids
            return {
                'domain': {
                    'location_id': [('inherit_location_id', 'in', stock_location_ids)]
                }
            }

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """
        Define harvesting employee based on selected team_id.
        """
        team_id = self.payrollffb_id.team_id.id
        current_worker = []
        if team_id:
            hr_member_ids = self.env['estate.hr.member'].search([('team_id', '=', team_id)])
            for member in hr_member_ids:
                current_worker.append(member.employee_id.id)
            return {
                'domain': {'employee_id': [('id', 'in', current_worker)]}
            }