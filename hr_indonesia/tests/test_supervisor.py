# -*- coding: utf-8 -*-

from openerp import api
from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError

class TestSupervisorLevel(TransactionCase):

    def setUp(self):
        super(TestSupervisorLevel, self).setUp()
        self.Supervisor = self.env['hr_indonesia.supervisor']
        self.val = {'name': 'President Director', 'code': 'PDR', 'sequence': 1}

    def test_00_create_supervisor(self):
        """ Check supervisor level object"""
        supervisor = self.Supervisor.create(self.val)
        self.assertTrue(supervisor, 'Supervisor failed.')

    def test_00_check_code(self):
        """ Check code length."""
        supervisor = self.Supervisor.create(self.val)

        # I edited less than 3 characters long
        supervisor.write({'code':'X'})
        self.assertLessEqual(len(supervisor.code), 3, 'Supervisor code more than 3 character long')

        # I edited more than 3 characters long
        with self.assertRaises(ValidationError):
            supervisor.write({'code': 'XXXX'})
