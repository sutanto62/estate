# -*- coding: utf-8 -*-
from openerp import api
from openerp.tests import TransactionCase
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError

class TestFingerprint(TransactionCase):

    def setUp(self):
        super(TestFingerprint, self).setUp()

        # setup
        self.Fingerprint = self.env['hr_fingerprint_ams.attendance']

        # create action reason
        reasons = ['Cuti', 'Sakit', 'Ijin', 'Dinas Luar', 'Keluar Kantor', 'Pulang Cepat']
        for r in reasons:
            self.env['hr.action.reason'].create({
                'action_type': 'action',
                'name': r
            })

        # create PKWTT Monthly
        self.employee_id = self.env['hr.employee'].create({
            'name': 'Employee',
            'nik_number': '1234567890',
            'contract_type': '1',
            'contract_period': '1'
        })
        self.today = datetime.today().strftime(DF)

        self.vals = {
            'db_id': 1,
            'terminal_id': 123456789,
            'nik': '1234567890',
            'employee_name': 'Employee',
            'date': self.today,
            'sign_in': 8.25,
            'sign_out': 17.5,
            'hour_late': 0.0,
            'day_normal': 1,
            'day_finger': 1,
        }
        # self.fingerprint_id = self.env['hr_fingerprint_ams.attendance'].create(vals)

    def test_00_import_csv(self):
        """ I imported csv"""
        fingerprint_id = self.env['hr_fingerprint_ams.attendance'].create(self.vals)
        self.assertTrue(fingerprint_id)

    def test_00_complete_day_normal_finger(self):
        """ I checked pivot day normal and day finger"""
        self.employee_id['nik_number'] = '3234567890'
        self.vals['nik'] = '3234567890'
        self.vals['day_normal'] = 1
        self.vals['day_finger'] = 1

        # complete day normal and finger
        fingerprint_id = self.Fingerprint.create(self.vals)
        self.assertEqual(fingerprint_id.p_day_normal, 1)
        self.assertEqual(fingerprint_id.p_day_finger, 1)

    def test_00_single_day_normal(self):
        """ I checked pivot day finger."""
        self.employee_id['nik_number'] = '3234567890'
        self.vals['nik'] = '3234567890'
        self.vals['day_normal'] = 1
        self.vals['day_finger'] = 0

        # complete day normal and finger
        fingerprint_id = self.Fingerprint.create(self.vals)
        self.assertEqual(fingerprint_id.p_day_normal, 0)

    def test_00_single_day_finger(self):
        """ I checked attendance without day normal."""
        self.employee_id['nik_number'] = '3234567890'
        self.vals['nik'] = '3234567890'
        self.vals['day_normal'] = 0
        self.vals['day_finger'] = 1

        # do not create attendance without day normal
        with self.assertRaises(ValidationError):
            self.Fingerprint.create(self.vals)

    def test_00_hour_late(self):
        """ I checked hour late attendance."""

        # HO employee
        self.vals['nik'] = '1234567890'
        self.vals['sign_in'] = 8.75
        self.vals['hour_late'] = 0.25
        self.vals['work_schedules'] = 'Staff HO'

        fingerprint_id = self.Fingerprint.create(self.vals)

        self.assertEqual(fingerprint_id.hour_late_t, '00:15')
        self.assertEqual(fingerprint_id.p_hour_late, 0.010416667)
        self.assertEqual(fingerprint_id.p_hour_late_office, 15)

    def test_01_action_reason(self):
        """ I checked sick action reason."""
        self.employee_id['nik_number'] = '3234567890'
        self.vals['nik'] = '3234567890'
        self.vals['sign_in'] = 0.0
        self.vals['sign_out'] = 0.0

        # I created sick action reason
        self.vals['action_reason'] = 'Sakit'
        fingerprint_id = self.Fingerprint.create(self.vals)
        self.assertEqual(fingerprint_id.p_sick, 1)

        # I created leave action reason
        self.vals['action_reason'] = 'Cuti'
        fp_leave_id = self.Fingerprint.create(self.vals)
        self.assertEqual(fp_leave_id.p_leave, 1)

        # I created ijin action reason
        self.vals['action_reason'] = 'Ijin'
        fp_permit_id = self.Fingerprint.create(self.vals)
        self.assertEqual(fp_permit_id.p_permit, 1)

        # I created dinas luar action reason
        self.vals['action_reason'] = 'Dinas Luar'
        fp_biz_id = self.Fingerprint.create(self.vals)
        self.assertEqual(fp_biz_id.p_business_trip, 1)

        # I created non registered action reason
        self.vals['action_reason'] = 'Not Registered'
        self.assertFalse(self.Fingerprint.create(self.vals))
