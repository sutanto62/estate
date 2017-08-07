# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError
from datetime import date, datetime, time
from dateutil import relativedelta

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class ResourceCalendarTest(TransactionCase):

    def setUp(self):
        super(ResourceCalendarTest, self).setUp()

        schedule_obj = self.env['resource.calendar']
        schedule_attendance_obj = self.env['resource.calendar.attendance']

        self.date_from = date.today() + relativedelta.relativedelta(month=1, day=1)
        self.date_to = date.today() + relativedelta.relativedelta(month=12, day=31)

        val = {
            'name': 'Schedule Single Attendance Weekdays',
            'attendance_ids': [
                (0, 0, {'name': 'Monday', 'dayofweek': '0', 'hour_from': 1.0, 'hour_to': 14.0,
                        'date_from': self.date_from, 'date_to': self.date_to}),
                (0, 0, {'name': 'Tuesday', 'dayofweek': '1', 'hour_from': 2.0, 'hour_to': 14.1,
                        'date_from': self.date_from, 'date_to': self.date_to}),
                (0, 0, {'name': 'Wednesday', 'dayofweek': '2', 'hour_from': 3.0, 'hour_to': 14.2,
                        'date_from': self.date_from, 'date_to': self.date_to}),
                (0, 0, {'name': 'Thursday', 'dayofweek': '3', 'hour_from': 4.0, 'hour_to': 14.3,
                        'date_from': self.date_from, 'date_to': self.date_to}),
                (0, 0, {'name': 'Friday 1', 'dayofweek': '4', 'hour_from': 5.0, 'hour_to': 11.5,
                        'date_from': self.date_from, 'date_to': self.date_to}),
                (0, 0, {'name': 'Friday 2', 'dayofweek': '4', 'hour_from': 3.0, 'hour_to': 16.4,
                        'date_from': self.date_from, 'date_to': self.date_to}),
                (0, 0, {'name': 'Saturday', 'dayofweek': '5', 'hour_from': 6.0, 'hour_to': 14.5,
                        'date_from': self.date_from, 'date_to': self.date_to}),
                (0, 0, {'name': 'Sunday', 'dayofweek': '6', 'hour_from': 7.0, 'hour_to': 14.6,
                        'date_from': self.date_from, 'date_to': self.date_to}),
            ]
        }

        self.single_attendance_schedule = schedule_obj.create(val)


    def test_00_get_day_work_from(self):
        """ Get a day work from of calendar attendances."""

        today = datetime.today()
        day = 0
        for att in self.single_attendance_schedule.attendance_ids:
            if day == int(att.dayofweek):
                date = today + relativedelta.relativedelta(weekday=int(att.dayofweek))
                res = self.single_attendance_schedule.get_day_work_from(date)
                self.assertEqual(res, att.hour_from)
                day += 1
            else:
                # multi attendances in single a day of week
                continue

    def test_00_get_day_work_to(self):
        """ Get a day work to of calendar attendances."""
        today = datetime.today()
        day = 0
        for att in self.single_attendance_schedule.attendance_ids:
            if day == int(att.dayofweek):
                date = today + relativedelta.relativedelta(weekday=int(att.dayofweek))
                res = self.single_attendance_schedule.get_day_work_to(date)
                self.assertEqual(res, att.hour_to)
                day += 1
            else:
                # multi attendances in single a day of week
                continue