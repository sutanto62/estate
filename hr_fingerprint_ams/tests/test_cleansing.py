# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError, AccessError
from openerp import SUPERUSER_ID
from datetime import datetime, timedelta, tzinfo
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from math import floor
import pytz

class TestCleansing(TransactionCase):

    def setUp(self):
        super(TestCleansing, self).setUp()
        self.Fingerprint = self.env['hr_fingerprint_ams.attendance']

    def test_cleansing(self):
        # Friday
        vals = {
            'employee_name': 'Abas Akumali',
            'nik': '3011000042',
            'time_start': 7.0,
            'time_end': 12.0,
            'date': '2018-03-09'
        }

        # Check if cleansing returned type error (multiple schedule shift within single calendar)
        with self.assertRaises(TypeError):
            self.Fingerprint.cleansing(vals)

        # Check if cleansing fix time start and end
        self.env.ref('hr_time_labour.schedule_day_1').active = False
        self.Fingerprint.cleansing(vals)
        self.assertEqual(vals['time_start'], 6.0)
        self.assertEqual(vals['time_end'], 11.0)

    def test_fix_day_in_out(self):
        """ Check time start and time end based on contract calendar."""

        contract_id = self.env.ref('estate_payroll.hr_contract_abasakumali_1')

        # Check if multiple schedule shift return value error
        with self.assertRaises(ValueError):
            self.Fingerprint._fix_day_in_out(contract_id, 5)

        # Check if schedule shift return value after deactivated double schedule shift
        self.env.ref('hr_time_labour.schedule_day_1').active = False
        time_start, time_end = self.Fingerprint._fix_day_in_out(contract_id, 5)
        self.assertEqual(time_start, 6.0)
        self.assertEqual(time_end, 11.0)