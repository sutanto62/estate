# -*- coding: utf-8 -*-

from openerp import models, fields, tools, api, _
from exceptions import ValueError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime

class Calendar(models.Model):
    """ Setup at employee's contract"""

    _inherit = "resource.calendar"

    holiday_ids = fields.One2many('hr_time_labour.holiday', inverse_name='calendar_id', string='Holiday')

    def _get_day_in_out(self, day=None):
        """Built-in Odoo employee working calendar did not support complex condition (schedule, shift, punch/flex)"""

        # prevent error when day is empty
        if day is None:
            return False
        
        day_num = int(day)
        # transform number to day
        day_name = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

        schedule_ids = self.env['hr_time_labour.schedule'].search([('calendar_id', '=', self.id)])

        # a calendar might have multiple shift
        schedule_shift_id = self.env['hr_time_labour.schedule_shift'].search([('schedule_id', 'in', schedule_ids.ids),
                                                                              ('day', '=', day)])

        # calendar has no schedule shift
        if not schedule_shift_id:
            name = day_name[day_num] if day_num < 7 else 'out of range'
            err_msg = _('No schedule shift found for %s') % name
            raise ValueError(err_msg)

        # prevent multiple shift returned
        if len(schedule_shift_id) > 1:
            err_msg = _('We found muptiple schedule shift for %s') % (day_name[day_num])
            raise ValueError(err_msg)

        time_start = schedule_shift_id.time_start
        time_end = schedule_shift_id.time_end

        return time_start, time_end

    def get_day(self, str_date):
        """
        Harvesting required to know if a date is working day, public holiday or friday
        :param date: date
        :param type: string
        :return: string [holiday, friday, workday]
        :rtype: string
        """

        res = ''
        date = datetime.strptime(str_date, DF)

        holiday_ids = self.holiday_ids.mapped('date')
        attendance_ids = self.attendance_ids.mapped('dayofweek')

        if len([s for s in holiday_ids if str_date in s]) or date.weekday() == 6:
            # holiday have higher precedence
            res = 'holiday'
        elif len([s for s in attendance_ids if str(date.weekday()) in s]):
            # friday is half day
            res = 'friday' if date.weekday() == 4 else 'workday'

        return res

class CalendarHoliday(models.Model):
    """ Odoo holiday is employee leave. Need new object for public holiday"""

    _name = 'hr_time_labour.holiday'
    _description = 'Public Holiday'
    _order ='date asc'

    calendar_id = fields.Many2one('resource.calendar', string='Calendar', ondelete='cascade')
    name = fields.Char('Public Holiday', required=True)
    date = fields.Date('Date', required=True)
