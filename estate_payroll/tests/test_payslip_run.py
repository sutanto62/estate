# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from hr_fingerprint_ams import *


class TestPayslipRun(TransactionCase):

    def setUp(self):
        super(TestPayslipRun, self).setUp()
        self.PayslipRun = self.env['hr.payslip.run']
        self.Wage = self.env['estate.wage']
        self.Upkeep = self.env['estate.upkeep']
        self.Activity = self.env['estate.upkeep.activity']
        self.Labour = self.env['estate.upkeep.labour']
        self.Material = self.env['estate.upkeep.material']
        self.Config = self.env['estate.config.settings']

        # self.Fingerprint = self.env['hr_fingerprint_ams.fingerprint']
        # self.Attendance = self.env['hr.attendance']
        self.UpkeepLabour = self.env['estate.upkeep.labour']

        self.date_1 = (datetime.datetime.today() + relativedelta.relativedelta(months=-1, day=1)).strftime('%Y-%m-%d')
        self.date_2 = (datetime.datetime.today() + relativedelta.relativedelta(day=1, months=0, days=-1)).strftime('%Y-%m-%d')
        self.demo = self.env.ref('estate.estate_upkeep_2')
        self.assistant_id = self.env.ref('hr.employee_al')
        self.team_id = self.env.ref('estate.team_syukur')
        self.estate_id = self.env.ref('stock.stock_main_estate')
        self.division_id = self.env.ref('stock.stock_division_1')
        self.khl_1 = self.env.ref('estate.khl_1')


        # Upkeep Data
        config_val = {
            'default_max_entry_day': 100
        }
        self.config = self.Config.create(config_val)

        wage_val = {
            'name': 'UMR Regional 2016',
            'active': True,
            'date_start': self.date_1,
            'estate_id': self.estate_id.id,
            'wage': 1875000,
            'number_of_days': 25,
            'overtime_amount': 10000,
        }
        self.wage = self.Wage.create(wage_val)

        upkeep_val = {
            'name': 'BKM',
            'assistant_id': self.team_id.id,
            'team_id': self.assistant_id.id,
            'date': self.date_1,
            'estate_id': self.estate_id.id,
            'division_id': self.division_id.id,
        }
        self.upkeep = self.Upkeep.create(upkeep_val)

        # Fingerprint
        # fingerprint_val = {
        #     'db_id': 1537,
        #     'terminal_id': 301100224,
        #     'nik': '3011000224',
        #     'employee_name': 'Abas Akumali',
        #     'auto_assign': True,
        #     'date': self.date_1,
        #     'work_schedules': 'KebunSen&amp;Sab',
        #     'time_start': 6,
        #     'time_end': 14,
        #     'sign_in': 3.02,
        #     'sign_out': 14.6,
        #     'day_normal': 1,
        #     'day_finger': 1,
        #     'hour_overtime': 0,
        #     'hour_work': 8,
        #     'required_in': True,
        #     'required_out': True,
        #     'department': 'Liyodu (Kurni Y. Latada)',
        #     'hour_attendance': 9.58,
        #     'hour_ot_normal': 0,
        # }
        # self.FingerprintAttendance = self.env['hr_fingerprint_ams.attendance']
        # self.fingerprint_attendance = self.FingerprintAttendance.create(fingerprint_val)

        # Payslip Run
        payslip_run_val = {
            'name': 'Payroll',
            'date_start': self.date_1,
            'date_end': self.date_2,
            'type': 'estate',
            'estate_id': self.env.ref('stock.stock_main_estate').id,
            'slip_ids': [
                (0, 0, {
                    'name': 'SLIP/001',
                    'employee_id': self.env.ref('hr_employee.khl_1').id,
                    'date_from': self.date_1,
                    'date_to': self.date_2,
                    'struct_id': self.env.ref('hr_payroll.structure_estate_pkwt_d').id,
                    'contract_id': self.env.ref('estate_payroll.hr_contract_abasakumali_1').id
                }),
                (0, 0, {
                    'name': 'SLIP/002',
                    'employee_id': self.env.ref('hr_employee.khl_1').id,
                    'date_from': self.date_1,
                    'date_to': self.date_2,
                    'struct_id': self.env.ref('hr_payroll.structure_estate_pkwt_d').id,
                    'contract_id': self.env.ref('estate_payroll.hr_contract_abasdepo_1').id
                })
            ]
        }
        self.payslip_run = self.PayslipRun.create(payslip_run_val)
        self.payslip_run_demo = self.env.ref('estate_payroll.estate_payroll_1')

    def test_00_create(self):
        """ Check state """
        # self.assertTrue(self.wage)
        # self.assertTrue(self.config)
        # self.assertTrue(self.upkeep)
        # self.assertTrue(self.fingerprint_attendance)
        self.assertTrue(self.payslip_run)

        # Payslip create in draft state
        self.assertEqual(self.payslip_run.state, 'draft', 'Estate Payroll: payslip batches created not in draft')
        for payslip in self.payslip_run.slip_ids:
            self.assertEqual(payslip.state, 'draft', 'Estate Payroll: payslip created not in draft')

    # todo test run failed run close_payslip_run()
    # def test_00_close_payslip_run(self):
    #     # Imitate when human resources manager close payslip batch
    #     self.payslip_run_demo.close_payslip_run()
    #     self.assertEqual(self.payslip_run_demo.state, 'close', 'Estate Payslip: close_payslip_run did not close payslip run')
    #     for payslip in self.payslip_run_demo.slip_ids:
    #         self.assertEqual(payslip.state, 'close', 'Estate Payslip: close_payslip_run did not close payslip')

    # def test_00_draft_payslip_run(self):
    #     self.payslip_run.draft_payslip_run()
    #     self.assertEqual(self.payslip_run.state, 'draft',
    #                      'Estate Payslip: draft_payslip_run did not draft payslip run')
    #     for payslip in self.payslip_run.slip_ids:
    #         self.assertEqual(payslip.state, 'draft', 'Estate Payslip: draft_payslip_run did not draft payslip')
    #
    # def test_00_unlink(self):
    #     pass