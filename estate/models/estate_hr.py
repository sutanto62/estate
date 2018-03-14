# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import openerp.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError, UserError

class Team(models.Model):
    """Group of Estate Employee. Responsible to Assistant.

    Constraints:
    1. An employee is allowed to lead one active team.
    2. An employee is not allowed to have double job (leader and member) in a single team.
    3. An employee is allowed to register as member of one active team."""

    _name = 'estate.hr.team'
    _inherit = 'mail.thread'

    name = fields.Char("Team Name")
    complete_name = fields.Char("Complete Name")
    active = fields.Boolean("Active", default="True")
    date_effective = fields.Date("Date Effective")
    employee_id = fields.Many2one('hr.employee', "Team Leader", required='True', ondelete='restrict',
                                  help="An employee is only allowed to lead one active team.")
    assistant_id = fields.Many2one('hr.employee', "Assistant", ondelete='restrict',
                                   help="Set this as default Assistant, will be used to record at Upkeep.", track_visibility="onchange")
    division_id = fields.Many2one('stock.location', "Division",
                                  domain=[('estate_location', '=', True), ('estate_location_level', '=', '2')],
                                  help="Define default division when create upkeep record.", track_visibility="onchange")
    member_ids = fields.One2many('estate.hr.member', 'team_id')
    member_total = fields.Integer(compute='_count_member', store='False')
    state = fields.Selection([('draft', 'Draft'),
                              ('active', 'Active'),
                              ('suspend', 'Suspend')], "State",
                             default="draft",
                             help='Active team allowed to be used as upkeep team.', track_visibility="onchange")

    @api.depends('member_ids')
    def _count_member(self):
        # Count amount member
        val = 0
        for i in self.member_ids:
            val += 1
        self.member_total = val
        # validate double member
        # print 'Validate double member'

    @api.constrains('employee_id', 'member_ids')
    def _validate_leader(self):
        """Validate team leader.
        1. An employee is allowed to lead one active team.
        2. An employee is not allowed to have double job (leader and member) in a single team.
        3. An employee is allowed to register as member of one active team."""

        if self.employee_id:
            # Validate if Leader has been registered at another team
            res = self.search([('id', 'not in', self.ids),
                               ('employee_id', '=', self.employee_id.id),
                               ('state', '=', 'active')])
            if res:
                msg = _('%s is a leader at Team %s' % (self.employee_id.name, res.name))
                raise ValidationError(msg)

        if self.member_ids:
            for rec in self.member_ids:
                # validate double job
                if self.employee_id == rec.employee_id:
                    date_effective = datetime.strptime(self.date_effective, '%Y-%m-%d')
                    current_contract = self.env['hr.contract'].current(self.employee_id,
                                                                       date_effective)
                    if current_contract.is_probation(date_effective):
                        return True
                    else:
                        msg = _('%s has been registered as a Team Leader.' % rec.employee_id.name)
                        raise ValidationError(msg)
                # todo error in validating in another team
                # constrains: add double team (config)
                # validate double team
                # res = self.env['estate.hr.member'].search([('team_id.state', '=', 'active'),
                #         ('employee_id', '=', rec.employee_id.id)])
                # msg = '%s has been registered in another active Team.' % rec.employee_id.name
                # raise ValidationError(msg)

    @api.multi
    def toggle_active(self):
        """ Active team should not be archived."""
        start = (datetime.today() + relativedelta(day=1)).strftime(DF)
        end = (datetime.today() + relativedelta(months=1, day=1, days=-1)).strftime(DF)
        for team in self:
            if self.env['estate.upkeep'].search([('team_id', '=', team.id),
                                                 ('date', '>=', start),
                                                 ('date', '<=', end)]):
                err_msg = _('Do not archived active team.')
                raise UserError(err_msg)

        return super(Team, self).toggle_active()

    @api.multi
    def unlink(self):
        """ Payslip will not displayed labour under deleted team."""

        today = datetime.today()
        start = (today + relativedelta(day=1)).strftime(DF)
        end = (today + relativedelta(months=1, day=1, days=-1)).strftime(DF)

        for team in self:
            if self.env['estate.upkeep'].search([('team_id', '=', team.id), ('date', '>=', start), ('date', '<=', end)]):
                # error when there are active upkeeps
                err_msg = _('You should not delete active team within the period.')
                raise UserError(err_msg)
            elif self.env['estate.upkeep'].search([('team_id', '=', team.id)]):
                # error when there were upkeeps
                err_msg = _('You should use archive instead of delete.')
                raise UserError(err_msg)

        return super(Team, self).unlink()

class TeamMember(models.Model):
    """List of Team Member
    """
    _name = 'estate.hr.member'

    team_id = fields.Many2one('estate.hr.team', "Team", ondelete='restrict')
    employee_id = fields.Many2one('hr.employee', "Labour", ondelete='restrict',
                                  help="Member should not be a Team Leader or other team member.")
    nik_number = fields.Char(related='employee_id.nik_number', store=True, readonly=True)
    contract_type = fields.Selection(related='employee_id.contract_type', store=False)
    contract_period = fields.Selection(related='employee_id.contract_period', store=False)

    @api.constrains('employee_id')
    def _check_employee(self):
        """ """
        # prevent differences between upkeep labor wage (weekly closing) and payslip (monthly)
        contract_id = self.env['hr.contract'].current(self.employee_id)
        if not contract_id:
            err_msg = _('Do not add %s without active contract.' % self.employee_id.name)
            raise ValidationError(err_msg)

        # prevent a labor registered into more than a team
        team_ids = self.env['estate.hr.member'].search([('id', '!=', self.ids),
                                                        ('employee_id', '=', self.employee_id.id)])
        if team_ids:
            err_msg = _('%s has been registered at others team.' % self.employee_id.name)
            raise ValidationError(err_msg)

    @api.multi
    def unlink(self):
        """ Payslip miscalculated payroll."""
        today = datetime.today()
        start = (today + relativedelta(day=1)).strftime(DF)
        end = (today + relativedelta(months=1, day=1, days=-1)).strftime(DF)

        for member in self:
            if self.env['estate.upkeep.labour'].search([('employee_id', '=', member.employee_id.id),
                                                        ('upkeep_date', '>=', start),
                                                        ('upkeep_date', '<=', end)]):
                err_msg = _('Don\'t delete %s as upkeep labour detected within the period.\n'
                            'Press ok or discard button to cancel.' % member.employee_id.name)
                raise UserError(err_msg)

        return super(TeamMember, self).unlink()

    @api.multi
    def current_labour(self, start=None, end=None):
        """ Check if team member has active upkeep labour."""
        if not start:
            start = (datetime.today() + relativedelta(day=1)).strftime(DF)

        if not end:
            end = (datetime.today() + relativedelta(months=1, day=1, days=-1)).strftime(DF)

        for member in self:
            return self.env['estate.upkeep.labour'].search_count([('employee_id', '=', member.employee_id.id)])

    @api.multi
    def move(self, target):
        """ Unlink and move to another team."""
        for member in self:
            vals = {
                'employee_id': member.employee_id.id,
                'team_id': target.id
            }
            # Delete first
            member.unlink()

            # Create
            return self.env['estate.hr.member'].create(vals)

class AttendanceCode(models.Model):
    _name = 'estate.hr.attendance'
    _rec_name = 'code'

    name = fields.Char('Attendance')
    code = fields.Char('Code')
    contract = fields.Boolean('Contract Based', help='No worked day recorded.')
    unit_amount = fields.Float('Hour')
    qty_ratio = fields.Float('Quantity Ratio', help='Use to calculate worked day quantity.')
    piece_rate = fields.Boolean('Piece Rate Day', help='Worked day recorded. Payroll as piece rate.')

    @api.onchange('contract')
    def _onchange_contract(self):
        """
        Contract based should not calculated hours and qty_ratio
        """
        if self.contract and self.piece_rate:
            self.unit_amount = 0
            self.qty_ratio = 0
            self.piece_rate = False

            warning = {
                'title': _('Warning!'),
                'message': _('Contract deactivated Piece Rate Day and reset Hour and Quantity Ratio.'),
            }

            return {'warning': warning}

    @api.onchange('piece_rate')
    def _onchange_piece_rate(self):
        """
        Piece rate based should calculated hours and qty_ratio - reset contract field.
        """
        if self.piece_rate and self.contract:
            self.contract = False

            warning = {
                'title': _('Warning!'),
                'message': _('Piece Rate Day deactivated Contract.'),
            }

            return {'warning': warning}

    @api.multi
    @api.constrains('qty_ratio', 'unit_amount')
    def check_piece_rate(self):
        if self.piece_rate:
            if not self.qty_ratio or not self.unit_amount:
                warning = {
                    'title': _('Warning!'),
                    'message': _('Quantity Ratio and Hour should be defined.'),
                }

                return {'warning': warning}

        return True


class Wage(models.Model):
    """Set default wage for estate level.
    """
    _name = 'estate.wage'
    _order = 'estate_id asc, date_start desc'
    _inherit = 'mail.thread'

    @api.multi
    @api.depends('wage', 'number_of_days')
    def _compute_daily_wage(self):
        for record in self:
            record.daily_wage = record.wage / record.number_of_days

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)
    date_start = fields.Date('Start Date', track_visibility="onchange")
    estate_id = fields.Many2one('stock.location', "Estate", track_visibility="onchange",
                                help='Set wage for all child locations if employee has no contract.',
                                domain=[('estate_location', '=', True), ('estate_location_level', '=', '1')])
    wage = fields.Float('Minimum Regional Wage', track_visibility="onchange")
    daily_wage = fields.Float('Daily Wage', help='Minimum Regional Wage divide by Number of working days',
                              compute='_compute_daily_wage')
    number_of_days = fields.Float('Number of working days', default='25', track_visibility="onchange")
    comment = fields.Text('Additional Information')
    overtime_amount = fields.Float('Flat Overtime', digits=dp.get_precision('Account'), track_visibility="onchange")

    @api.multi
    def get_current_overtime(self, estate):
        """
        Required to get current overtime by calling public method
        :param estate: estate instances
        :return: float
        """
        today = datetime.today().strftime(DF)
        current = self.env['estate.wage'].search([('active', '=', True), ('date_start', '<=', today), ('estate_id', '=', estate.id)],
                              order='date_start desc', limit=1)
        for record in current:
            if record.overtime_amount:
                return record.overtime_amount
            else:
                return 0
        return False
