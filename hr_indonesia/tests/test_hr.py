# -*- coding: utf-8 -*-

from openerp import api
from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError

class TestMasterActivity(TransactionCase):

    def setUp(self):
        super(TestMasterActivity, self).setUp()
        self.Employee = self.env['hr.employee']

    def test_00_employee_check_employee(self):
        """Employee should have unique NIK and Identification"""

        person_cindy = {'name': 'Cindy', 'nik_number': '', 'identification_id': ''}
        person_crawford = {'name': 'Crawford', 'nik_number': '', 'identification_id': ''}
        person_jack = {'name': 'Jack', 'nik_number': '22', 'identification_id': '33'}
        person_pieter = {'name': 'Pieter', 'nik_number': '22', 'identification_id': ''}
        person_parker = {'name': 'Pieter', 'nik_number': '', 'identification_id': '33'}

        # I create an employee without NIK or Identification
        self.assertTrue(self.Employee.create(person_cindy))

        # I create second employee without NIK or Identification
        self.assertTrue(self.Employee.create(person_crawford))

        # I create an employee with NIK and Identification
        self.assertTrue(self.Employee.create(person_jack))

        # I create an employee with double NIK
        with self.assertRaises(ValidationError):
            self.assertTrue(self.Employee.create(person_pieter))

        # I create an employee with double Identification
        with self.assertRaises(ValidationError):
            self.assertTrue(self.Employee.create(person_parker))