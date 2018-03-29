# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
import datetime
from dateutil import relativedelta
from openerp.exceptions import AccessError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from hr_fingerprint_ams import *


class TestSecurity(TransactionCase):

    def setUp(self):
        super(TestSecurity, self).setUp()

        self.PayslipRun = self.env['hr.payslip.run']

        self.Wage = self.env['estate.wage']
        self.Upkeep = self.env['estate.upkeep']
        self.Activity = self.env['estate.upkeep.activity']
        self.Labour = self.env['estate.upkeep.labour']
        # self.UpkeepLabour = self.env['estate.upkeep.labour']
        self.Material = self.env['estate.upkeep.material']
        self.Config = self.env['estate.config.settings']


        self.date_1 = (datetime.datetime.today() + relativedelta.relativedelta(months=-1, day=1)).strftime('%Y-%m-%d')
        self.date_2 = (datetime.datetime.today() + relativedelta.relativedelta(day=1, months=0, days=-1)).strftime('%Y-%m-%d')
        self.max_day = 1000
        self.demo = self.env.ref('estate.estate_upkeep_2')
        self.assistant_id = self.env.ref('hr.employee_al')
        self.team_id = self.env.ref('estate.team_syukur')
        self.estate_id = self.env.ref('stock.stock_main_estate')
        self.division_id = self.env.ref('stock.stock_division_1')
        self.khl_1 = self.env.ref('estate.khl_1')
        self.khl_2 = self.env.ref('estate.khl_2')

        # User
        User = self.env['res.users'].with_context({'no_reset_password': True})
        group_payroll_officer = self.ref('estate_payroll.estate_payroll_officer')
        group_payroll_assistant = self.ref('estate_payroll.estate_payroll_assistant')
        group_estate_user = self.ref('estate.group_user')
        group_estate_assistant = self.ref('estate.group_assistant')

        self.payroll_officer = User.create({
            'name': 'Meiske', 'login': 'meiske', 'alias_name': 'meiske', 'email': 'meiske@meiske.com',
            'groups_id': [(6, 0, [group_payroll_officer])]})
        self.payroll_assistant = User.create({
            'name': 'Mimin Gunawan', 'login': 'mimin', 'alias_name': 'mimin', 'email': 'mimin@mimin.com',
            'groups_id': [(6, 0, [group_payroll_assistant])]})
        self.estate_assistant = User.create({
            'name': 'Asisten Kebun', 'login': 'asisten', 'alias_name': 'asisten', 'email': 'asisten@asisten.com',
            'groups_id': [(6, 0, [group_estate_assistant])]})

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
            'max_day': self.max_day
        }
        self.upkeep = self.Upkeep.create(upkeep_val)

        # Payslip Run
        self.val = {
            'name': 'Payroll',
            'date_start': self.date_1,
            'date_end': self.date_2,
            'type': 'estate',
            'estate_id': self.ref('stock.stock_main_estate'),
            'slip_ids': [
                (0, 0, {
                    'name': 'SLIP/001',
                    'employee_id': self.khl_1.id,
                    'date_from': self.date_1,
                    'date_to': self.date_2,
                    'struct_id': self.ref('hr_payroll.structure_estate_pkwt_d'),
                    'contract_id': self.ref('estate.hr_contract_abasakumali_1')
                }),
                (0, 0, {
                    'name': 'SLIP/002',
                    'employee_id': self.khl_2.id,
                    'date_from': self.date_1,
                    'date_to': self.date_2,
                    'struct_id': self.ref('hr_payroll.structure_estate_pkwt_d'),
                    'contract_id': self.ref('estate.hr_contract_abasdepo_1')
                })
            ]
        }

        # self.payslip_run = self.PayslipRun.create(payslip_run_val)
        # self.payslip_run_demo = self.env.ref('estate_payroll.estate_payroll_1')

    def test_01_estate_payroll_officer(self):
        """ Check that only estate payroll officer can create payroll run."""

        # Payroll office created payslip run.
        payslip_run = self.PayslipRun.sudo(self.payroll_officer).create(self.val)
        self.assertTrue(payslip_run, 'Payroll officer unable to create payslip run.')
        payslip_run.unlink()

        # Payroll assistant created payslip run.
        payslip_run = self.PayslipRun.sudo(self.payroll_assistant).create(self.val)
        self.assertTrue(payslip_run, 'Payroll assistant unable to create payslip run.')
        payslip_run.unlink()

        # Estate assistant created payslip run
        with self.assertRaises(AccessError):
            payslip_run = self.PayslipRun.sudo(self.estate_assistant).create(self.val)


