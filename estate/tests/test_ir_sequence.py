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

    def test_01_generate_nik(self):
        """ Generate employee identification number."""
        reg_pkwt = str(1)+datetime.strftime(datetime.now(),'%y')

        company_id = self.browse_ref('base.main_company')

        person_cindy = {'name': 'Cindy', 'company_id': company_id.id,
                        'contract_period': '1', 'contract_type': '1'}

        person_crawford = {'name': 'Cindy', 'company_id': company_id.id, 'contract_period': '2', 'contract_type': '2',
                           'estate_id': self.browse_ref('base.main_company').id}
        person_jack = {'name': 'Cindy', 'company_id': None, 'contract_period': '1', 'contract_type': None}
        person_pieter = {'name': 'Cindy', 'company_id': None, 'contract_period': None, 'contract_type': '1'}

        # I created PKWT Monthly
        val = self.Employee.create(person_cindy)
        self.assertEqual(val.nik_number[:3], reg_pkwt)

        # I created PKWTT Daily
        val = self.Employee.create(person_crawford)
        self.assertEqual(val.nik_number[:4], '3011')