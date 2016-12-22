# -*- coding: utf-8 -*-

from openerp import api
from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError
from datetime import datetime


class TestSequence(TransactionCase):

    def setUp(self):
        super(TestSequence, self).setUp()
        self.Company = self.env['res.company']
        self.Estate = self.env['stock.location']
        self.Employee = self.env['hr.employee']
        self.Sequence = self.env['ir.sequence']

        # self.company = '01'
        # self.estate = '1'
        self.company_code = '01'
        self.estate_code = '1'

        # self.company = self.browse_ref('base.main_company')
        self.company = self.env['res.company'].search([('name', '=', 'HJA')])

        self.estate = self.browse_ref('estate.estate').id
        self.pkwtt = '1'
        self.pkwt = '2'
        self.monthly = '1'
        self.daily = '2'
        self.internship = True
        self.outsource = True

        self.str_year = datetime.now().strftime('%y')

    def test_01_create_nik_khl(self):
        """ Employee ID prefixed with character 3"""
        company_code = '01'
        estate_code = '1'

        khl = {
            'name': 'KHL',
            'contract_type': self.pkwt,
            'contract_period': self.daily,
            'company_id': self.company.id,
            'estate_id': self.estate
        }

        khl_no_company = {
            'name': 'KHL no Company',
            'contract_type': self.pkwt,
            'contract_period': self.daily,
            'estate_id': self.estate,
        }

        khl_no_estate = {
            'name': 'KHL no Company',
            'contract_type': self.pkwt,
            'contract_period': self.daily,
            'company_id': self.company.id,
        }

        # I created KHL employee (PKWT Daily)
        khl_id = self.Employee.create(khl)
        if khl_id.nik_number:
            self.assertEqual(len(khl_id.nik_number), 10, 'Employee ID should have 10 length of character')
            self.assertEqual(khl_id.nik_number[0], '3', 'Segment 1 should be 3')
            self.assertEqual(khl_id.nik_number[1:3], company_code, 'Segment 2 should be ' + company_code)
            self.assertEqual(khl_id.nik_number[3:4], estate_code, 'Segment 3 should be ' + estate_code)
        else:
            self.assertFalse(khl_id.nik_number, 'Employee ID should not been created')

        # I created KHL employee without company
        khl_no_company_id = self.Employee.create(khl_no_company)
        self.assertFalse(khl_no_company_id.nik_number, 'Employee ID should not been created')

        # I created KHL employee without estate
        khl_no_estate_id = self.Employee.create(khl_no_estate)
        self.assertFalse(khl_no_estate_id.nik_number, 'Employee ID should not been created')

    def test_02_update_nik(self):
        """ Generate new employee identification number."""

        vals = {
            'name': 'KHL',
            'contract_type': self.pkwt,
            'contract_period': self.daily,
            'company_id': self.company.id,
            'estate_id': self.estate,
        }

        # I created KHL employee (PKWT Daily)
        khl_id = self.Employee.create(vals)
        if khl_id.nik_number:
            self.assertEqual(len(khl_id.nik_number), 10, 'Employee ID should have 10 length of character')
            self.assertEqual(khl_id.nik_number[0], '3', 'Segment 1 should be 3')
            self.assertEqual(khl_id.nik_number[1:3], self.company_code, 'Segment 2 should be ' + self.company_code)
            self.assertEqual(khl_id.nik_number[3:4], self.estate_code, 'Segment 3 should be ' + self.estate_code)
        else:
            self.assertFalse(khl_id.nik_number, 'Employee ID should not been created')

        # I promote KHL to PKWTT Monthly
        new_vals = {
            'contract_type': self.pkwtt,
            'contract_period': self.monthly,
            'company_id': self.company.id,
            'estate_id': self.estate,
        }
        khl_id.write(new_vals)
        self.assertEqual(len(khl_id.nik_number), 10, 'Employee ID should have 10 length of character')
        self.assertEqual(khl_id.nik_number[0], '1', 'Segment 1 should be 1')
        self.assertEqual(khl_id.nik_number[1:3], self.str_year, 'Segment 2 should be ' + self.str_year)


    # def test_01_generate_nik(self):
    #     """ Generate employee identification number."""
    #     reg_pkwt = str(1)+datetime.strftime(datetime.now(),'%y')
    #
    #     company_id = self.browse_ref('base.main_company')
    #
    #     person_cindy = {'name': 'Cindy', 'company_id': company_id.id,
    #                     'contract_period': '1', 'contract_type': '1'}
    #
    #     person_crawford = {'name': 'Cindy', 'company_id': company_id.id, 'contract_period': '2', 'contract_type': '2',
    #                        'estate_id': self.browse_ref('base.main_company').id}
    #     person_jack = {'name': 'Cindy', 'company_id': None, 'contract_period': '1', 'contract_type': None}
    #     person_pieter = {'name': 'Cindy', 'company_id': None, 'contract_period': None, 'contract_type': '1'}
    #
    #     # I created PKWT Monthly
    #     val = self.Employee.create(person_cindy)
    #     self.assertEqual(val.nik_number[:3], reg_pkwt)
    #
    #     # I created PKWTT Daily
    #     val = self.Employee.create(person_crawford)
    #     self.assertEqual(val.nik_number[:4], '3011')