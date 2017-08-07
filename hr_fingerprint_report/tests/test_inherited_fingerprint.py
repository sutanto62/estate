# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError
from datetime import date, datetime, time
from dateutil import relativedelta
from decimal import *

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT


class FingerprintTest(TransactionCase):

    def setUp(self):
        super(FingerprintTest, self).setUp()

        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        work_schedule_obj = self.env['resource.calendar']
        self.fingerprint_obj = self.env['hr_fingerprint_ams.attendance']

        self.date_from = date.today() + relativedelta.relativedelta(month=1, day=1)
        self.date_to = date.today() + relativedelta.relativedelta(month=12, day=31)

        self.val_schedule_daily = {
            'name': 'schedule a',
            'attendance_ids': [
                (0, 0, {'name': 'Monday', 'dayofweek': '0', 'hour_from': 6, 'hour_to': 14,
                        'date_from': self.date_from, 'date_to': self.date_to}),
                (0, 0, {'name': 'Tuesday', 'dayofweek': '1', 'hour_from': 6, 'hour_to': 14,
                        'date_from': self.date_from, 'date_to': self.date_to}),
                (0, 0, {'name': 'Wednesday', 'dayofweek': '2', 'hour_from': 6, 'hour_to': 14,
                        'date_from': self.date_from, 'date_to': self.date_to}),
                (0, 0, {'name': 'Thursday', 'dayofweek': '3', 'hour_from': 6, 'hour_to': 14,
                        'date_from': self.date_from, 'date_to': self.date_to}),
                (0, 0, {'name': 'Friday', 'dayofweek': '4', 'hour_from': 6, 'hour_to': 12,
                        'date_from': self.date_from, 'date_to': self.date_to}),
                (0, 0, {'name': 'Saturday', 'dayofweek': '5', 'hour_from': 6, 'hour_to': 14,
                        'date_from': self.date_from, 'date_to': self.date_to}),
                (0, 0, {'name': 'Sunday', 'dayofweek': '6', 'hour_from': 6, 'hour_to': 14,
                        'date_from': self.date_from, 'date_to': self.date_to}),
            ]
        }

        self.contract_type = {
            'name': 'Daily'
        }
        self.person_daily = {
            'name': 'Person - Daily',
            'contract_type': '2',
            'contract_period': '2',
            'nik_number': '3011700001'
        }
        self.person_daily_contract = {
            'wage': 2500000,
            'name': 'Contract Daily',
            'date_start': self.date_from,
            'date_end': self.date_to,
        }

        self.contract_type_id = self.env['hr.contract.type'].create(self.contract_type)
        self.schedule_id = work_schedule_obj.create(self.val_schedule_daily)
        self.person_daily_id = employee_obj.create(self.person_daily)
        self.person_daily_contract['employee_id'] = self.person_daily_id.id
        self.person_daily_contract['working_hours'] = self.schedule_id.id
        self.contract_id = contract_obj.create(self.person_daily_contract)

        self.val_fingerprint = {
            'employee_name': str(self.person_daily_id.name),
            'nik': self.person_daily_id.nik_number,
            'db_id': 1,
            'terminal_id': 301170001,
            'date': date.today().strftime(DF),
        }

    # def test_01_compute_employee(self):
    #     """ Get work schedules based on contract's period as fingerprint."""
    #     employee_obj = self.env['hr.employee']
    #     contract_obj = self.env['hr.contract']
    #     work_schedule_obj = self.env['resource.calendar']
    #     fingerprint_obj = self.env['hr_fingerprint_ams.attendance']
    #     contract_type_id = self.env['hr.contract.type'].create(self.contract_type)
    #
    #     schedule_a = work_schedule_obj.create(self.val_schedule_daily)
    #     self.assertTrue(schedule_a)
    #
    #     employee_id = employee_obj.create(self.person_daily)
    #     self.assertTrue(employee_id)
    #
    #     val = {
    #         'employee_name': str(employee_id.name),
    #         'nik': employee_id.nik_number,
    #         'db_id': 1,
    #         'terminal_id': 301170001,
    #         'date': date.today().strftime(DF),
    #         'sign_in': 5.3,
    #         'sign_out': 14.30,
    #     }
    #     fingerprint_id = fingerprint_obj.create(val)
    #     self.assertTrue(fingerprint_id)
    #
    #     # Employee has no contract
    #     self.assertFalse(fingerprint_id.contract_id.id)
    #
    #     # Employee has single contract
    #     person_daily_contract = {
    #         'wage': 2500000,
    #         'employee_id': employee_id.id,
    #         'type_id': contract_type_id.id,
    #         'name': 'Contract Daily',
    #         'date_start': self.date_from,
    #         'date_end': self.date_to,
    #         'working_hours': schedule_a.id
    #     }
    #     contract_id = contract_obj.create(person_daily_contract)
    #     self.assertTrue(contract_id)
    #     self.assertEqual(fingerprint_id.contract_id.id, contract_id.id, 'Wrong contract.')
    #
    #     # Employee has multiple contracts
    #     future_date_start = date.today() + relativedelta.relativedelta(years=1, month=1, day=1)
    #     future_date_end = date.today() + relativedelta.relativedelta(years=1, month=12, day=31)
    #     second_contract = {
    #         'wage': 2500000,
    #         'employee_id': employee_id.id,
    #         'type_id': contract_type_id.id,
    #         'name': 'Contract Daily',
    #         'date_start': future_date_start,
    #         'date_end': future_date_end,
    #         'working_hours': schedule_a.id,
    #     }
    #     second_contract_id = contract_obj.create(second_contract)
    #     fingerprint_id._compute_employee()
    #     self.assertNotEqual(fingerprint_id.contract_id.id, second_contract_id.id, 'Wrong contract.')
    #
    #     # Second fingerprint, second contract
    #     val = {
    #         'employee_name': str(employee_id.name),
    #         'nik': employee_id.nik_number,
    #         'db_id': 1,
    #         'terminal_id': 301170001,
    #         'date': (date.today() + relativedelta.relativedelta(years=1)).strftime(DF),
    #         'sign_in': 5.3,
    #         'sign_out': 14.30,
    #     }
    #     second_fingerprint_id = fingerprint_obj.create(val)
    #     self.assertEqual(second_fingerprint_id.contract_id.id, second_contract_id.id, 'Wrong contract.')

    def test_01_float_to_datetime(self):
        """ Test float to datetime."""
        fingerprint_obj = self.env['hr_fingerprint_ams.attendance']

        # positive float, return positive time
        val_positive = 5.5
        self.assertEqual(fingerprint_obj.float_to_datetime(val_positive), '05:30')

        # positive float, return positive time
        val_negative = -5.5
        self.assertEqual(fingerprint_obj.float_to_datetime(val_negative), '05:30')

        # empty vals, return False
        val_empty = ''
        self.assertEqual(fingerprint_obj.float_to_datetime(val_empty), False)

        # zero val, return False for 0
        val_zero = 0
        self.assertEqual(fingerprint_obj.float_to_datetime(val_empty), False)

    def test_01_compute_pivot(self):
        """ Check pivot field"""

        getcontext().prec = 8

        fingerprint = {
            'employee_name': str(self.person_daily_id.name),
            'nik': self.person_daily_id.nik_number,
            'db_id': 1,
            'terminal_id': 301170001,
            'date': date.today().strftime(DF),
            'sign_in': 5.25,
            'sign_out': 14.25,
            'day_normal': 1,
            'day_finger': 1,
            'hour_late': 0,
        }

        fingerprint_id = self.env['hr_fingerprint_ams.attendance'].create(fingerprint)
        self.assertTrue(fingerprint_id)

        # KHT/L only have sign_in
        fingerprint_id.write({'action_reason': '', 'sign_out': 0, 'day_finger': 0})
        fingerprint_id._compute_pivot()
        self.assertEqual(fingerprint_id.p_day_normal, 0)

        # KHT/L only have sign_out
        fingerprint_id.write({'action_reason': '', 'sign_in': 0, 'sign_out': 14, 'day_finger': 0})
        fingerprint_id._compute_pivot()
        self.assertEqual(fingerprint_id.p_day_normal, 0)

        # Riil is empty
        fingerprint_id.write({'day_finger': ''})
        fingerprint_id._compute_pivot()
        self.assertEqual(fingerprint_id.p_day_normal, 0)

        # Riil is 0
        fingerprint_id.write({'day_finger': 0})
        fingerprint_id._compute_pivot()
        self.assertEqual(fingerprint_id.p_day_normal, 0)

        # Column1 late
        fingerprint_id.write({'hour_late': 2.25})
        fingerprint_id._compute_time()
        fingerprint_id._compute_pivot()
        self.assertEqual(fingerprint_id.p_hour_late, 0.09375)
        self.assertEqual(fingerprint_id.p_hour_late_office, 0)

        # Column1 late with RO SenJum, RO Sabtu, Sec Pagi, Sec Malam
        fingerprint_id.write({'hour_late': 2.25, 'work_schedules': 'RO SenJum'})
        fingerprint_id._compute_time()
        fingerprint_id._compute_pivot()
        self.assertEqual(fingerprint_id.p_hour_late, 0.09375)
        self.assertEqual(fingerprint_id.p_hour_late_office, 135)

        # Column5 late more than 5 minutes
        self.assertEqual(fingerprint_id.p_late_amount_office, 1)

        # Column5 late less than 5 minutes
        fingerprint_id.write({'hour_late': 0.07})
        fingerprint_id._compute_time()
        fingerprint_id._compute_pivot()
        self.assertEqual(fingerprint_id.p_late_amount_office, 0)

        # Plg. Cepat (mnt)
        fingerprint_id.write({'hour_early_leave': 0.5})
        fingerprint_id._compute_time()
        fingerprint_id._compute_pivot()
        self.assertEqual(fingerprint_id.p_hour_early_leave, 0)
        self.assertEqual(fingerprint_id.p_early_leave, 30)

        # fingerprint_id.write({'work_schedules': 'RO SenJum', 'p_hour_late': '00:15'})
        # fingerprint_id._compute_pivot()
        # print fingerprint_id.work_schedules
        # print fingerprint_id.p_hour_late_office
        # self.assertEqual(fingerprint_id.p_column5, 1)


    # delete
    # def test_01_get_time_start(self):
    #     """ Check returned time_start as working schedules"""
    #     fingerprint = {
    #         'employee_name': str(self.person_daily_id.name),
    #         'nik': self.person_daily_id.nik_number,
    #         'db_id': 1,
    #         'terminal_id': 301170001,
    #         'date': date.today().strftime(DF),
    #         'sign_in': 5.3,
    #         'sign_out': 14.30,
    #     }
    #
    #     fingerprint_id = self.env['hr_fingerprint_ams.attendance'].create(fingerprint)
    #     self.assertTrue(fingerprint_id)
    #     today = date.today().strftime(DF)
    #     print 'schedule work from %s and work to %s' % (self.schedule_id.get_day_work_from,
    #                                                     self.schedule_id.get_day_work_to)
    #     self.assertEqual(fingerprint_id._get_time(self.schedule_id, today), 6, 'Wrong hour from.')
    #     self.assertEqual(fingerprint_id._get_time(self.schedule_id, today, 2),
    #                      12 if date.today().weekday() == 4 else 14, 'Wrong hour to.')


    def test_01_timevalue(self):
        fingerprint = {
            'employee_name': str(self.person_daily_id.name),
            'nik': self.person_daily_id.nik_number,
            'db_id': 1,
            'terminal_id': 301170001,
            'date': date.today().strftime(DF),
            'sign_in': 5.25,
            'sign_out': 14.25,
            'day_normal': 1,
            'day_finger': 1,
        }

        fingerprint_id = self.env['hr_fingerprint_ams.attendance'].create(fingerprint)
        self.assertTrue(fingerprint_id)

        # there is hour late
        fingerprint_id.write({'hour_late': 2.5})
        fingerprint_id._compute_time()
        fingerprint_id._compute_pivot()
        self.assertEqual(fingerprint_id.p_hour_late, 0.10416667)

        # there is no hour late
        fingerprint_id.write({'hour_late': 0})
        fingerprint_id._compute_time()
        fingerprint_id._compute_pivot()
        self.assertEqual(fingerprint_id.p_hour_late, 0)

    def test_01_get_early_leave(self):
        """ Check early leave return """
        today = datetime.today()
        fingerprint = {
            'employee_name': str(self.person_daily_id.name),
            'nik': self.person_daily_id.nik_number,
            'db_id': 1,
            'terminal_id': 301170001,
            'date': today.strftime(DF),
            'sign_in': 5.25,
            'sign_out': 14.5,
            'day_normal': 1,
            'day_finger': 1,
        }

        fingerprint_id = self.env['hr_fingerprint_ams.attendance'].create(fingerprint)
        hour_to = fingerprint_id.schedule_id.get_day_work_to(today)
        self.assertTrue(fingerprint_id)

        fingerprint_id.write({'sign_out': 9.25})
        fingerprint_id._compute_time()
        fingerprint_id._compute_pivot()
        self.assertEqual(fingerprint_id.p_labor_early_leave, 0)

        fingerprint_id.write({'sign_out': 10.25})
        fingerprint_id._compute_time()
        fingerprint_id._compute_pivot()
        self.assertEqual(fingerprint_id.p_labor_early_leave,0)

    def test_02_sign_in_out(self):
        """ Employee has complete sign_in and sign_out."""
        fingerprint = self.val_fingerprint
        fingerprint['sign_in'] = 5
        fingerprint['sign_out'] = 14

        fingerprint_id = self.fingerprint_obj.create(fingerprint)

        self.assertTrue(fingerprint_id)