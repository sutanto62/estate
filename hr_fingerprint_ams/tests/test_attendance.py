# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError, AccessError
from openerp import SUPERUSER_ID
from datetime import datetime, timedelta, tzinfo
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from math import floor
import pytz


class TestAttendance(TransactionCase):

    def setUp(self):
        super(TestAttendance, self).setUp()
        self.Fingerprint = self.env['hr_fingerprint_ams.fingerprint']
        self.FingerprintAttendance = self.env['hr_fingerprint_ams.attendance']
        self.Attendance = self.env['hr.attendance']
        self.UpkeepLabour = self.env['estate.upkeep.labour']

        self.Schedule = self.env['hr_time_labour.schedule'].create(dict(
            name='Kebun',
            code='KBN',
            overnight_schedule=False,
        ))

        self.labour = self.env['hr.employee'].create(dict(
            name='Labour',
            nik_number=1234567890,
            active=True,
        ))

        self.action_reason = self.env['hr.action.reason'].create(dict(
            name='Leave',
            action_type='action',
            active=True,
            action_duration=8.0
        ))

        self.vals = {
            'db_id': 1537,
            'terminal_id': 301100224,
            'nik': 3011000224,
            'employee_name': 'Abas Akumali',
            'auto_assign': True,
            'date': '2016-01-01',
            'work_schedules': 'Kebun',
            'time_start': 6,
            'time_end': 14,
            'sign_in': 3.02,
            'sign_out': 14.6,
            'day_normal': 1,
            'day_finger': 1,
            'hour_overtime': 0,
            'hour_work': 8,
            'required_in': True,
            'required_out': True,
            'department': 'Liyodu (Kurni Y. Latada)',
            'hour_attendance': 9.58,
            'hour_ot_normal': 0,
            'action_reason': '',
        }

        self.finger_in_out = dict(
            db_id=123,
            terminal_id=123456789,
            employee_name='Labour',
            nik=1234567890,
            sign_in=6.2,
            sign_out=14.06,
            date='2016-01-01',
            action_reason='',
            work_schedules='Kebun'
        )

    def test_01_create_complete_fingerprint(self):
        """ Create and import fingerprint attendance"""
        vals = self.finger_in_out

        # I created a normal fingerprint (employee, nik, sign_in and sign_out)
        fingerprint = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'}).create(vals)
        self.assertTrue(fingerprint, 'Fingerprint did not created.')

        # I checked attendance
        for attendance in fingerprint.attendance_ids:
            self.assertTrue(attendance)
            self.assertTrue(attendance.action in ('sign_in', 'sign_out', 'action'), 'Action did not belong to in/out/action.')
        self.assertEqual(len(fingerprint.attendance_ids), 2, 'Fingerprint did not create in and out attendance.')

    def test_02_create_not_complete_fingerprint(self):
        """ Create fingerprint with sign_in or sign_out only without action"""
        vals = self.finger_in_out

        # I created data without sign_in
        vals['sign_in'] = 0

        # I created a normal fingerprint (employee, nik, sign_in and sign_out)
        fingerprint = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'}).create(vals)
        self.assertFalse(fingerprint, 'Fingerprint should not created.')

        # I created data without sign_out
        vals['sign_out'] = 0

        # I created a normal fingerprint (employee, nik, sign_in and sign_out)
        fingerprint = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'}).create(vals)
        self.assertFalse(fingerprint, 'Fingerprint should not created.')

    def test_03_create_action_fingerprint(self):
        """ Create fingerprint with an action reason"""
        vals = self.finger_in_out

        vals['sign_in'] = 0
        vals['action_reason'] = 'Leave'

        # I created action reason for first time sign-in/out
        fingerprint = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'}).create(vals)
        self.assertTrue(fingerprint)

        # I checked attendance
        for attendance in fingerprint.attendance_ids:
            self.assertTrue(attendance)
            self.assertTrue(attendance.action in ('sign_in', 'sign_out', 'action'),
                            'Action did not belong to in/out/action.')
        self.assertEqual(len(fingerprint.attendance_ids), 1, 'Fingerprint did not create in and out attendance.')

    def test_04_create_action_fingerprint_no_employee_found(self):
        """ No employee no fingerprint"""
        vals = self.finger_in_out
        vals['action_reason'] = 'Leave'
        vals['employee_name'] = 'No Name'

        # I created action reason for first time sign-in/out
        fingerprint = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'}).create(vals)
        self.assertFalse(fingerprint)


    def test_04_create_overnight_fingerprint(self):
        """ Create overnight schedule"""
        # schedule_1 = self.env['hr_time_labour.schedule'].create(dict(
        #     name='Waker Siang',
        #     code='WKS',
        #     overnight_schedule=False,
        # ))
        #
        # schedule_2 =self.env['hr_time_labour.schedule'].create(dict(
        #     name='Waker Malam',
        #     code='WKM',
        #     overnight_schedule=True,
        # ))
        #
        # vals = self.finger_in_out
        #
        # # I created regular attendance
        # vals['sign_in'] = 19
        # vals['sign_out'] = 6
        # vals['work_schedules'] = 'Waker Siang'
        # vals['action_reason'] =  ''
        #
        # print 'vals %s' % vals
        #
        # fingerprint_kebun = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'}).create(vals)
        # self.assertFalse(fingerprint_kebun)

    def test_05_update_complete_fingerprint(self):
        """ Update fingerprint"""
        vals = self.finger_in_out

        # I created a normal fingerprint (employee, nik, sign_in and sign_out)
        fingerprint = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'}).create(vals)
        self.assertTrue(fingerprint, 'Fingerprint did not created.')

        # I checked attendance
        for attendance in fingerprint.attendance_ids:
            self.assertTrue(attendance)
            self.assertTrue(attendance.action in ('sign_in', 'sign_out', 'action'),
                            'Action did not belong to in/out/action.')

        # I changed imported sign_in and sign_out time
        fingerprint_id = fingerprint.id
        self.assertEqual(fingerprint.state, 'draft', 'Fingerprint should be draft.')

        vals['sign_in'] = 5
        vals['sign_out'] = 15

        fingerprint = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'}).create(vals)
        self.assertEqual(fingerprint.id, fingerprint_id, 'Fingerprint failed to update existing record')
        self.assertEqual(fingerprint.sign_in, 5, 'Fingerprint failed to update sign_in.')
        self.assertEqual(fingerprint.sign_out, 15, 'Fingerprint failed to update sign_out.')

        for attendance in fingerprint.attendance_ids:
            if attendance.action == 'sign_in':
                self.assertEqual(attendance.name, '2015-12-31 22:00:00')
            elif attendance.action == 'sign_out':
                self.assertEqual(attendance.name, '2016-01-01 08:00:00')

    def test_06_update_not_complete_fingerprint(self):
        """ Update existing fingerprint's sign_in to 0."""
        vals = self.finger_in_out

        # I created a normal fingerprint (employee, nik, sign_in and sign_out)
        fingerprint = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'}).create(vals)

        # I change imported no action reason nor sign_in
        vals['sign_in'] = 0
        fingerprint = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'}).create(vals)
        self.assertFalse(fingerprint, 'Fingerprint should not be created.')

    def test_07_update_action_reason_fingerprint(self):
        """ Update existing fingerprint's sign_in 0 with action reason"""
        vals = self.finger_in_out

        # I created a normal fingerprint (employee, nik, sign_in and sign_out)
        fingerprint = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'}).create(vals)

        # I change imported no action reason nor sign_in
        vals['sign_in'] = 0
        vals['action_reason'] = 'Leave'
        fingerprint = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'}).create(vals)
        self.assertEqual(fingerprint.sign_in, 0, 'Fingerprint failed to update sign_in.')
        self.assertEqual(len(fingerprint.attendance_ids), 1, 'Fingerprint should return only 1 attendance.')
        self.assertEqual(fingerprint.attendance_ids[0].action, 'action', 'Attendance should be an action.')

    def test_00_get_employee(self):
        """ Test to get active employee using name and employee identification number."""
        self.labour_ok = self.env['hr.employee'].create(dict(
            name='Abas Akumali',
            nik_number=3011000224,
            active=True
        ))

        self.labour_ok = self.env['hr.employee'].create(dict(
            name='Abas Depo',
            nik_number=3011000225,
            active=False
        ))

        # Returned existing
        employee_id = self.FingerprintAttendance._get_employee('Abas Akumali', 3011000224)
        self.assertTrue(employee_id, 'Employee not found.')

        # I searched non active name
        employee_id = self.FingerprintAttendance._get_employee('Abas Depo', 3011000225)
        self.assertFalse(employee_id, 'It should not return unactive employee.')

        # I searched non exist name
        employee_id = self.FingerprintAttendance._get_employee('Abas', 3011000224)
        self.assertFalse(employee_id, 'It should not return employee.')

        # I searched non exist nik
        employee_id = self.FingerprintAttendance._get_employee('Abas Akumali', 3011000230)
        self.assertFalse(employee_id, 'It should not return employee.')

    def test_00_get_name(self):
        att_date = '2016-01-01'
        att_time = 6.2
        utc_datetime = datetime(2015, 12, 31, 23, 12, 0, 0, pytz.utc)

        fingerprint = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'})

        # I checked UTC date
        self.assertEqual(fingerprint._get_name(att_date, att_time), utc_datetime)

        # I checked empty date
        self.assertEqual(fingerprint._get_name('', att_time), None)

    def test_08_approve_all(self):
        """ Test single level approval by hr officer group"""
        hrstaff = self.env.ref('estate.hrstaff')
        estateuser = self.env.ref('estate.estate_user')
        vals = self.finger_in_out

        # I created a normal fingerprint (employee, nik, sign_in and sign_out)
        fingerprint = self.FingerprintAttendance.with_context({'tz': 'Asia/Jakarta'}).create(vals)
        self.assertTrue(fingerprint, 'Fingerprint did not created.')

        # Other user ValidationError
        with self.assertRaises(ValidationError):
            fingerprint.sudo(estateuser).approve_all_admin()

        fingerprint.sudo(hrstaff).approve_all_admin()
        self.assertEqual(fingerprint.state, 'approved')




