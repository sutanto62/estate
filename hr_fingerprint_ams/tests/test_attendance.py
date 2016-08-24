# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError
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

        self.finger_att_1 = self.env.ref('hr_fingerprint_ams.finger_att_1')
        self.finger_att_2 = self.env.ref('hr_fingerprint_ams.finger_att_2')

        self.khl_1 = self.env.ref('hr_employee.khl_1')

    def test_00_create(self):
        self.assertTrue(self.finger_att_1, 'HR Fingerprint AMS: create did not create fingerprint attendance')

    def test_00_create_attendance(self):
        sign_in = self.env['hr.attendance'].search([('id', 'in', self.finger_att_1.attendance_ids.ids),
                                                       ('action', '=', 'sign_in')])
        sign_out = self.env['hr.attendance'].search([('id', 'in', self.finger_att_1.attendance_ids.ids),
                                                       ('action', '=', 'sign_out')])

        self.assertTrue(sign_in, 'HR Fingerprint AMS: fingerprint attendance did not create sign in attendance')
        self.assertTrue(sign_out, 'HR Fingerprint AMS: fingerprint attendance did not create sign out attendance')

    def test_00_unlink(self):
        # Unlink fingerprint attedance with draft state
        self.assertTrue(self.finger_att_1.unlink(), 'HR Fingerprint AMS: cannot unlink draft fingerprint attendance')

        # Imitate fingerprint attendance with approved state
        self.finger_att_2.button_approved()
        with self.assertRaises(ValidationError):
            self.finger_att_2.unlink()

    def test_00_get_employee(self):
        employee = self.khl_1
        res = self.FingerprintAttendance._get_employee(employee.name)
        self.assertTrue(res.active)

    def test_00_get_name(self):
        fingerprint_attendance_date = self.finger_att_1.date
        fingerprint_attendance_time = self.finger_att_1.sign_in

        hour = int(floor(fingerprint_attendance_time))
        minute = int(round((fingerprint_attendance_time - hour) * 60))  # widget float_time use round
        second = '00'

        fingerprint_attendance = datetime.strptime(fingerprint_attendance_date + ' ' +
                                                   str(hour) + ':' +
                                                   str(minute) + ':' +
                                                   second, DT)

        attendance_id = self.env['hr.attendance'].search([('id', 'in', self.finger_att_1.attendance_ids.ids),
                                                          ('action', '=', 'sign_in')])

        attendance_utc = datetime.strptime(attendance_id.name, DT).replace(tzinfo=pytz.utc)

        local = pytz.timezone('Asia/Jakarta')
        attendance_local = attendance_utc.astimezone(local)

        self.assertEqual(fingerprint_attendance.strftime(DT), attendance_local.strftime(DT),
                         'HR Fingerprint: _get_name failed to convert UTC date to Local')

    def test_00_button_confirmed(self):
        self.finger_att_1.button_confirmed()
        self.assertEqual(self.finger_att_1.state, 'confirmed', 'HR Fingerprint: button_confirmed failed.')

    def test_00_button_approved(self):
        self.finger_att_1.button_approved()
        self.assertEqual(self.finger_att_1.state, 'approved', 'HR Fingerprint: button_approved failed.')
