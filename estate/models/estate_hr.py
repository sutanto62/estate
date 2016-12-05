# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime
import openerp.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from openerp.exceptions import ValidationError

class Team(models.Model):
    """Group of Estate Employee. Responsible to Assistant.

    Constraints:
    1. An employee is allowed to lead one active team.
    2. An employee is not allowed to have double job (leader and member) in a single team.
    3. An employee is allowed to register as member of one active team."""

    _name = 'estate.hr.team'
    _inherit = 'mail.thread'

    name = fields.Char("Team Name")
    complete_name = fields.Char("")
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
                msg = '%s is a leader at Team %s' % (self.employee_id.name, res.name)
                raise ValidationError(msg)

        if self.member_ids:
            for rec in self.member_ids:
                # validate double job
                if self.employee_id == rec.employee_id:
                    msg = '%s has been registered as a Team Leader.' % rec.employee_id.name
                    raise ValidationError(msg)
                # todo error in validating in another team
                # constrains: add double team (config)
                # validate double team
                # res = self.env['estate.hr.member'].search([('team_id.state', '=', 'active'),
                #         ('employee_id', '=', rec.employee_id.id)])
                # msg = '%s has been registered in another active Team.' % rec.employee_id.name
                # raise ValidationError(msg)

class TeamMember(models.Model):
    """List of Team Member
    """
    _name = 'estate.hr.member'

    team_id = fields.Many2one('estate.hr.team', "Team", ondelete='restrict')
    employee_id = fields.Many2one('hr.employee', "Labour", ondelete='restrict',
                                  help="Member should not be a Team Leader.")
    nik_number = fields.Char(related='employee_id.nik_number', store=True, readonly=True)
    contract_type = fields.Selection(related='employee_id.contract_type', store=False)
    contract_period = fields.Selection(related='employee_id.contract_period', store=False)


class AttendanceCode(models.Model):
    _name = 'estate.hr.attendance'
    _rec_name = 'code'

    name = fields.Char('Attendance')
    code = fields.Char('Code')
    contract = fields.Boolean('Contract Based', help='Activate to remark contract based attendance.')
    unit_amount = fields.Float('Hour')
    qty_ratio = fields.Float('Quantity Ratio', help='Use to calculate work result quantity.')

    @api.onchange('contract')
    def _onchange_contract(self):
        """
        Contract based should not calculated hours and qty_ratio
        """
        if self.contract:
            self.unit_amount = 0
            self.qty_ratio = 0

            warning = {
                'title': _('Warning!'),
                'message': _('Hour and Quantity Ratio has been reset.'),
            }

            return {'warning': warning}


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
        today = datetime.today().strftime(DATE_FORMAT)
        current = self.env['estate.wage'].search([('active', '=', True), ('date_start', '<=', today), ('estate_id', '=', estate.id)],
                              order='date_start desc', limit=1)
        for record in current:
            if record.overtime_amount:
                return record.overtime_amount
            else:
                return 0
        return False