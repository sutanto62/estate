# -*- coding: utf-8 -*-

from openerp import models, fields, tools, api, _
from exceptions import ValueError

class Calendar(models.Model):
    """ Setup at employee's contract"""

    _inherit = "resource.calendar"

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
