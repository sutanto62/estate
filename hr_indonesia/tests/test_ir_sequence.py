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

        self.val_person = {
            'name': 'Abas Akumali',
            'company_id': self.browse_ref('base.main_company').id
        }

        # val_nik = {
        #     'name': 'Tes',
        #     'implementation': 'standard',
        #     'code': 'hr_indonesia.code',
        #     'active': True,
        #     'prefix': '%(code_1)s%(y)s',
        #     'padding': 7,
        #     'number_increment': 1,
        #     'number_next_actual': 1,
        # }
        #
        # sequence_nik = self.Sequence.create(val_nik)

    def test_00_generate_no_nik(self):
        """ No company, contract type and period."""

        person_cindy = {'name': 'Cindy', 'company_id': None, 'contract_period': None, 'contract_type': None}
        person_crawford = {'name': 'Cindy', 'company_id': '1', 'contract_period': None, 'contract_type': None}
        person_jack = {'name': 'Cindy', 'company_id': None, 'contract_period': '1', 'contract_type': None}
        person_pieter = {'name': 'Cindy', 'company_id': None, 'contract_period': None, 'contract_type': '1'}

        # I created employee without company, contract period and type
        self.assertFalse(self.Employee.create(person_cindy).nik_number)

        # I created employee with one of company, contract period and type
        self.assertFalse(self.Employee.create(person_crawford).nik_number)
        self.assertFalse(self.Employee.create(person_jack).nik_number)
        self.assertFalse(self.Employee.create(person_pieter).nik_number)

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