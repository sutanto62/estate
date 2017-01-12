# -*- coding: utf-8 -*-

from openerp import models, fields, tools, _


class Schedule(models.Model):

    _name = 'hr_time_labour.schedule'
    _description = 'Work Schedule'

    name = fields.Char('Schedule Name')
    code = fields.Char('Schedule Code')
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)
    effective_date = fields.Date('Effective Date')
    type = fields.Selection([('punch', 'Punch'),
                             ('elapsed', 'Elapsed'),
                             ('flex', 'Flex')],
                            string='Schedule Type',
                            help="* Elapsed, only elapsed punch type display on the Shift page \n"
                            "* Punch, In, Out, Break, Meal and Transfer punch types can be entered on the Shift page \n"
                            "* Flex, only In and Out punches can be entered.")
    rotating_schedule = fields.Boolean('Rotating Schedule', help='Define Rotating Schedule')
    overnight_schedule = fields.Boolean('Overnight Schedule', help="Allow sign-in or sign-out in different day")
    days_in_schedule = fields.Integer('Days in Schedule', help='Populate shift time')
    calendar_id = fields.Many2one('resource.calendar', string='Working Schedule',
                                  help='Link to Odoo Working Schedule at Contract')
    schedule_shift_ids = fields.One2many('hr_time_labour.schedule_shift', 'schedule_id', string='Schedule Shifts')


class ScheduleShift(models.Model):

    _name = 'hr_time_labour.schedule_shift'
    _description = 'Schedule Shifts'

    schedule_id = fields.Many2one('hr_time_labour.schedule', string='Schedule')
    shift_id = fields.Many2one('hr_time_labour.shift', string='Code')
    day = fields.Integer('Day')
    type = fields.Selection(related='shift_id.type', string='Type', readonly=True)
    time_start = fields.Float(related='shift_id.time_start', string='Time Start', readonly=True)
    time_end = fields.Float(related='shift_id.time_end', string='Time End', readonly=True)


class Shift(models.Model):

    _name = 'hr_time_labour.shift'
    _description = 'Shift'
    _rec_name = 'name'

    name = fields.Char('Shift Name')
    code = fields.Char('Shift Code')
    description = fields.Text('Description')
    active = fields.Boolean('Active')
    effective_date = fields.Date('Effective Date')
    off_shift = fields.Boolean('Off Shift', help='This shift is for off')
    type = fields.Selection([('punch', 'Punch'),
                             ('elapsed', 'Elapsed'),
                             ('flex', 'Flex')],
                            string='Shift Type',
                            help="* Elapsed, only elapsed punch type display on the Shift page \n"
                                 "* Punch, In, Out, Break, Meal and Transfer punch types can be entered on the Shift page \n"
                                 "* Flex, only In and Out punches can be entered."
                            )
    scheduled_hours = fields.Float('Scheduled Hours')
    time_start = fields.Float('Start Time')
    time_end = fields.Float('End Time')
    time_restriction_id = fields.Many2one('hr_time_labour.time_restriction', string='Time Restriction Rule')
    shift_time_ids = fields.One2many('hr_time_labour.shift_time', 'shift_id', string='Shift Time')


class ShiftTime(models.Model):

    _name = 'hr_time_labour.shift_time'
    _description = 'Shift Time'

    shift_id = fields.Many2one('hr_time_labour.shift')
    name = fields.Char('Shift Time Name')
    code = fields.Char('Shift Time Code')
    description = fields.Text('Description')
    type = fields.Selection([('in', 'In'),
                             ('out', 'Out'),
                             ('meal', 'Meal'),
                             ('break', 'Break'),
                             ('transfer', 'Transfer'),
                             ('elapsed', 'Elapsed')],
                            string='Punch/Elapsed Type')
    time = fields.Float('Time', help='Use only for punch and flex shifts')
    timezone = fields.Char('Timezone')
    duration = fields.Float('Duration', help='Duration of a punch to the next punch.')
    overnight = fields.Boolean('Overnight', default=False, help='Checked for overnight scheduled')


class Workday(models.Model):
    """
    Optional component of the schedule definition that adds descriptive information.
    Additionally a workday may be used by Global Payroll Rules as a code to identify the type of day.

    """
    _name = 'hr_time_labour.workday'
    _description = 'Workday'

    name = fields.Char('Workday Name')
    code = fields.Char('Workday Code')
    description = fields.Text('Description')
    active = fields.Boolean('Active')
    effective_date = fields.Date('Effective Date')


class TimeRestriction(models.Model):
    """ Restriction punch type """
    _name = 'hr_time_labour.time_restriction'
    _description = 'Shift Time Restriction'

    name = fields.Char('Restriction Name')
    code = fields.Char('Restriction Code')
    description = fields.Text('Description')
    active = fields.Boolean('Active')
    effective_date = fields.Date('Effective Date')
    early_in = fields.Float('Early In')  # None is no restriction
    late_in = fields.Float('Late In')
    early_meal = fields.Float('Early Meal')
    late_meal = fields.Float('Late Meal')
    early_out = fields.Float('Early Out')
    late_out = fields.Float('Late Out')