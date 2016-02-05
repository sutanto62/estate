# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions

class Team(models.Model):
    """Group of Estate Employee. Responsible to Assistant.

    Constraints:
    1. An employee is allowed to lead one active team.
    2. An employee is not allowed to have double job (leader and member) in a single team.
    3. An employee is allowed to register as member of one active team."""

    _name = 'estate.hr.team'

    name = fields.Char("Team Name")
    complete_name = fields.Char("")
    active = fields.Boolean("Active", default="True")
    date_effective = fields.Date("Date Effective")
    employee_id = fields.Many2one('hr.employee', "Team Leader", required='True', ondelete='restrict',
                                  help="An employee is only allowed to lead one active team.")
    member_ids = fields.One2many('estate.hr.member', 'team_id')
    member_total = fields.Integer(compute='_count_member', store='False')
    state = fields.Selection([('draft', 'Draft'),
                              ('active', 'Active'),
                              ('suspend', 'Suspend')], "State",
                             default="draft",
                             help='Active team allowed to be used as upkeep team.')

    @api.depends('member_ids')
    def _count_member(self):
        # Count total member
        val = 0
        for i in self.member_ids:
            val += 1
        self.member_total = val
        # validate double member
        print 'Validate double member'

    @api.constrains('employee_id', 'member_ids')
    def _validate_leader(self):
        """Validate team leader.
        1. An employee is allowed to lead one active team.
        2. An employee is not allowed to have double job (leader and member) in a single team.
        3. An employee is allowed to register as member of one active team."""

        if self.employee_id:
            # validate leader
            res = self.search([('employee_id', '=', self.employee_id.id), ('state', '=', 'active')])
            if res:
                msg = '%s is a leader at Team %s' % (self.employee_id.name, res.name)
                raise exceptions.ValidationError(msg)

        if self.member_ids:
            for rec in self.member_ids:
                # validate double job
                if self.employee_id == rec.employee_id:
                    msg = '%s has been registered as a Team Leader.' % rec.employee_id.name
                    raise exceptions.ValidationError(msg)
                # validate double team
                res = self.env['estate.hr.member'].search([('team_id.state', '=', 'active'),
                        ('employee_id', '=', rec.employee_id.id)])
                msg = '%s has been registered in another active Team.' % rec.employee_id.name
                raise exceptions.ValidationError(msg)

class TeamMember(models.Model):
    """List of Team Member
    """
    _name = 'estate.hr.member'

    team_id = fields.Many2one('estate.hr.team', "Team", ondelete='restrict')
    employee_id = fields.Many2one('hr.employee', "Labour", ondelete='restrict',
                                  help="Member should not be a Team Leader.")
    contract_type = fields.Selection(related='employee_id.contract_type', store=False)
    contract_period = fields.Selection(related='employee_id.contract_period', store=False)