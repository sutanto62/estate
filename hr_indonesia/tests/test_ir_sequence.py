# -*- coding: utf-8 -*-

from openerp import api
from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError
from datetime import datetime

class TestSequence(TransactionCase):

    def setUp(self):
        super(TestSequence, self).setUp()
        self.Employee = self.env['hr.employee']
        self.Sequence = self.env['ir.sequence']

        self.company = self.browse_ref('base.main_company').id
        self.pkwtt = '1'
        self.pkwt = '2'
        self.monthly = '1'
        self.daily = '2'
        self.internship = True
        self.outsource = True

        self.str_year = datetime.now().strftime('%y')

        self.val_person = {
            'name': 'Abas Akumali',
            'company_id': '',
            'contract_type': '',
            'contract_period': '',
            'internship': '',
            'outsource': ''
        }

    def test_00_create_nik_for_employee(self):
        """ Only employee has Employee Identity Number"""

        employee = {
                 'name': 'Employee',
                 'company_id': self.company,
                 'contract_type': self.pkwtt,
                 'contract_period': self.monthly
             }

        internship = {
            'name': 'Internship',
            'company_id': self.company,
            'contract_type': self.pkwtt,
            'contract_period': self.monthly,
            'internship': self.internship
        }

        outsource = {
            'name': 'Outsource',
            'company_id': self.company,
            'contract_type': self.pkwtt,
            'contract_period': self.monthly,
            'outsource': self.outsource
        }

        # I created employee
        employee_id = self.Employee.create(employee)
        self.assertTrue(employee_id.nik_number)

        # I created internship
        internship_id = self.Employee.create(internship)
        self.assertFalse(internship_id.nik_number, 'Internship should have no Employee Identity Number')

        # I created outsource
        outsource_id = self.Employee.create(outsource)
        self.assertFalse(outsource_id.nik_number, 'Outsource should have no Employee Identity Number')

    def test_01_check_nik_employee(self):
        """ Employee ID prefixed with character 1"""

        pkwtt = {
            'name': 'PKWTT Monthly',
            # 'company_id': self.company,
            'contract_type': self.pkwtt,
            'contract_period': self.monthly,
        }

        pkwtt_daily = {
            'name': 'PKWT Daily',
            # 'company_id': self.company,
            'contract_type': self.pkwtt,
            'contract_period': self.daily,
        }

        # I created PKWTT (Monthly)
        pkwtt_id = self.Employee.create(pkwtt)
        self.assertEqual(len(pkwtt_id.nik_number), 10, 'Employee ID should have 10 length of character')
        self.assertEqual(pkwtt_id.nik_number[0], '1', 'Segment 1 should be 1')
        self.assertEqual(pkwtt_id.nik_number[1:3], self.str_year, 'Segment 2 should be ' + self.str_year)

        # I created PKWTT (Daily) at certain year
        pkwtt_daily_id = self.Employee.with_context(ir_sequence_date='2015-10-01').create(pkwtt_daily)
        self.assertEqual(len(pkwtt_daily_id.nik_number), 10, 'Employee ID should have 10 length of character')
        self.assertEqual(pkwtt_daily_id.nik_number[0], '1', 'Segment 1 should be 1')
        self.assertEqual(pkwtt_daily_id.nik_number[1:3], '15', 'Segment 2 should be 15')

    def test_01_create_nik_contract(self):
        """ Employee ID prefixed with character 2"""

        contract = {
            'name': 'Contract',
            'contract_type': self.pkwt,
            'contract_period': self.monthly
        }

        # I created contract employee PKWT (Montly)
        contract_id = self.Employee.create(contract)
        self.assertEqual(len(contract_id.nik_number), 10, 'Employee ID should have 10 length of character')
        self.assertEqual(contract_id.nik_number[0], '2', 'Segment 1 should be 2')
        self.assertEqual(contract_id.nik_number[1:3], self.str_year, 'Segment 2 should be ' + self.str_year)



        # def test_00_create_employee_without_nik(self):
    #     """ No company, contract type and period."""
    #
    #     person_cindy = {'name': 'Cindy', 'company_id': None, 'contract_period': None, 'contract_type': None}
    #     person_crawford = {'name': 'Cindy', 'company_id': '1', 'contract_period': None, 'contract_type': None}
    #     person_jack = {'name': 'Cindy', 'company_id': None, 'contract_period': '1', 'contract_type': None}
    #     person_pieter = {'name': 'Cindy', 'company_id': None, 'contract_period': None, 'contract_type': '1'}
    #
    #     # I created employee without company, contract period and type
    #     self.assertFalse(self.Employee.create(person_cindy).nik_number)
    #
    #     # I created employee with one of company, contract period and type
    #     self.assertFalse(self.Employee.create(person_crawford).nik_number)
    #     self.assertFalse(self.Employee.create(person_jack).nik_number)
    #     self.assertFalse(self.Employee.create(person_pieter).nik_number)
    #
    # def test_01_create_employee_with_nik(self):
    #     ''' Generate auto NIK'''
    #     pkwtt_monthly = {'name': 'Cindy', 'company_id': 1, 'contract_period': '1', 'contract_type': '1'}
    #
    #     # I created an employee
    #     employee = self.Employee.create(pkwtt_monthly)
    #     self.assertTrue(employee.nik_number, 'No NIK generated.')
    #
    #     # I edit an employee
    #     employee.write({'contract_period': '2', 'contract_type': '2'})

        # I created employee with PKWT Monthly at Company 1

    # It should be testend under estate module (estate_id didn't exist yet)
    # def test_01_generate_nik(self):
    #     """ Generate employee identification number."""
    #     year = str(1)+datetime.strftime(datetime.now(),'%y')
    #     print 'year without centuries %s' % year
    #     person_cindy = {'name': 'Cindy', 'company_id': self.browse_ref('base.main_company').id,
    #                     'contract_period': '1', 'contract_type': '1'}
    #     person_crawford = {'name': 'Cindy', 'company_id': '1', 'contract_period': '2', 'contract_type': '2',
    #                        'estate_id': self.browse_ref('base.main_company').id}
    #     person_jack = {'name': 'Cindy', 'company_id': None, 'contract_period': '1', 'contract_type': None}
    #     person_pieter = {'name': 'Cindy', 'company_id': None, 'contract_period': None, 'contract_type': '1'}
    #
    #     # I created PKWT Monthly
    #     val = self.Employee.create(person_cindy)
    #     self.assertEqual(val.nik_number[:3], year)
    #
    #     # I created PKWTT Daily
    #     val = self.Employee.create(person_crawford)
    #     self.assertEqual(val.nik_number[:3], year)