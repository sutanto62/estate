# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions

class Team(models.Model):
    """Group of Estate Employee. Responsible to Assistant.
    """
    _name = 'estate.hr.team'

    name = fields.Char("Team Name")
    complete_name = fields.Char("")
    active = fields.Boolean("Active")
    date_effective = fields.Date("Date Effective")
    employee_id = fields.Many2one('hr.employee', "Team Leader", ondelete='restrict')
    member_ids = fields.One2many('estate.hr.member', 'team_id')
    member_total = fields.Integer(compute='_count_member', store='False')

    @api.depends('member_ids')
    def _count_member(self):
        # Count total member
        val = 0
        for i in self.member_ids:
            val += 1
        self.member_total = val
        # validate double member
        print 'Validate double member'

    @api.constrains('employee_id')
    def _validate_employee(self):
        """Validate employee and member.
        1. An employee is allowed to lead one active team.
        2. An employee is allowed to register as member of one active team.
        3. An employee is not allowed to have double job (leader and member) in a single team."""

        if self.employee_id:
            res = self.search([('employee_id', '=', self.employee_id.id), ('active', '=', 'True')])
            if res:
                msg = '%s is a leader at Team %s' % (self.employee_id.name, res.name)
                raise exceptions.ValidationError(msg)

    @api.onchange('member_ids')
    def _onchange_member_ids(self):
        if self.member_ids:
            print 'Cek anggota kemandoran.'

class TeamMember(models.Model):
    """List of Team Member
    """
    _name = 'estate.hr.member'

    team_id = fields.Many2one('estate.hr.team', "Team", ondelete='restrict')
    employee_id = fields.Many2one('hr.employee', "Labour", ondelete='restrict')
    contract_type = fields.Selection(related='employee_id.contract_type', store=False)
    contract_period = fields.Selection(related='employee_id.contract_period', store=False)