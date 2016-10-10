# -*- coding: utf-8 -*-

from openerp import models, fields, tools, _


class Schedule(models.Model):
    _name = 'hr_time_labour.schedule'
    _description = 'Work Schedule'

    name = fields.Char('Schedule Name')
    code = fields.Char('Schedule Code')
    description = fields.Text('Description')
    active = fields.Boolean('Active')
    effective_date = fields.Date('Effective Date')
    type = fields.Selection([('punch', 'Punch'),
                             ('elapsed', 'Elapsed'),
                             ('flex', 'Flex')],
                            string='Schedule Type',
                            help="* Elapsed, only elapsed punch type display on the Shift page \n"
                            "* Punch, In, Out, Break, Meal and Transfer punch types can be entered on the Shift page \n"
                            "* Flex, only In and Out punches can be entered.")
    rotating_schedule = fields.Boolean('Rotating Schedule', help='Define Rotating Schedule')
    days_in_schedule = fields.Integer('Days in Schedule')


class Shift(models.Model):
    _name = 'hr_time_labour.shift'
    _description = 'Shift'

    name = fields.Char('Shift Name')
    code = fields.Char('Shift Code')
    description = fields.Text('Description')
    active = fields.Char('Active')
    effective_date = fields.Date('Effective Date')
    off_shift = fields.Boolean('Off Shift', help='This shift is for off')
    type = fields.Selection([('punch', 'Punch'),
                             ('elapsed', 'Elapsed'),
                             ('flex', 'Flex')],
                            string='Shift Type')
    scheduled_hours = fields.Float('Scheduled Hours', widget='time')
    time_start = fields.Float('Start Time')
    time_end = fields.Float('End Time')


class ShiftTime(models.Model):
    _name = 'hr_time_labour.shift_time'
    _description = 'Shift Time'

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
    duration = fields.Float('Duration')


class Workday(models.Model):
    _name = 'hr_time_labour.workday'
    _description = 'Workday'

    name = fields.Char('Workday Name')
    code = fields.Char('Workday Code')
    description = fields.Text('Description')
    active = fields.Boolean('Active')
    effective_date = fields.Date('Effective Date')




