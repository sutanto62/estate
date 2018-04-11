# -*- coding: utf-8 -*-

from openerp import api
from openerp.tests import TransactionCase
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError, AccessError

class TestInheritedResource(TransactionCase):

    def setUp(self):
        super(TestInheritedResource, self).setUp()

        self.Calendar = self.env['resource.calendar']
        self.calendar_id = self.env.ref('hr_time_labour.schedule_day_4').calendar_id
        self.calendar = self.env.ref('resource.timesheet_group1')

    def test_get_day_in_out(self):
        """ Check day in out."""

        # Check if calling without parameter return false
        self.assertFalse(self.calendar_id._get_day_in_out(), 'Empty paramater should return False.')

        # Check if monday returned 6.0 and 14.0
        time_start, time_end = self.calendar_id._get_day_in_out(0)
        self.assertEqual(time_start, 6.0)
        self.assertEqual(time_end, 14.0)

        # Check if friday which has multiple schedule shift returned value error
        with self.assertRaises(ValueError):
            self.calendar_id._get_day_in_out(4)

        # Check if out of range returned value error
        with self.assertRaises(ValueError):
            self.calendar_id._get_day_in_out(10)

        # Check if friday returned 6.0 and 11.0
        self.env.ref('hr_time_labour.schedule_day_1').active = False
        self.env.ref('hr_time_labour.schedule_day_1_4').active = False
        time_start, time_end = self.calendar_id._get_day_in_out(4)
        self.assertEqual(time_start, 6.0)
        self.assertEqual(time_end, 11.0)

    def test_get_day(self):
        """ Check day returned."""

        str_workday = '2018-04-16'
        str_friday = '2018-04-20'
        str_holiday = '2018-02-14'
        str_sunday = '2018-04-15'

        # check holiday
        self.assertEqual(self.calendar.get_day(str_holiday), 'holiday')
        self.assertEqual(self.calendar.get_day(str_sunday), 'holiday')

        # check friday
        self.assertEqual(self.calendar.get_day(str_friday), 'friday')

        # check if workday returned true
        self.assertEqual(self.calendar.get_day(str_workday), 'workday')


