# -*- coding: utf-8 -*-
from openerp import api
from openerp.tests import TransactionCase
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError, AccessError

class TestLha(TransactionCase):

    def setUp(self):
        super(TestLha, self).setUp()

        self.Employee = self.env['hr.employee']
        self.Block = self.env['estate.block.template']
        self.User = self.env['res.users'].with_context({'no_reset_password': True})

        (group_admin, group_assistant) = (self.ref('base.group_no_one'), self.ref('estate.group_assistant'))

        self.user_assistant = self.User.create({
            'name': 'Lukas', 'login': 'lukas', 'alias_name': 'lukas', 'email': 'lukas.petters@example.com',
            'groups_id': [(6, 0, [group_assistant])]})
        self.user_assistant_non_division = self.User.create({
            'name': 'Goodfinger', 'login': 'good', 'alias_name': 'good', 'email': 'good.finger@example.com',
            'groups_id': [(6, 0, [group_assistant])]})

        self.estate =  self.Block.create({
            'name': 'Estate',
            'estate_location': True,
            'estate_location_level': '1',
        })


        self.employee = self.Employee.create({
            'name': 'Assistant A',
            'user_id': self.user_assistant.id,
            'estate_id': self.estate.id
        })

        self.employee_b = self.Employee.create({
            'name': 'Assistant B',
            'user_id': self.user_assistant_non_division.id,
            'estate_id': self.estate.id
        })

        self.division_a = self.Block.create({
            'name': 'Division A',
            'assistant_id': self.employee.id,
            'estate_location': True,
            'estate_location_level': '2',
        })

        self.division_b = self.Block.create({
            'name': 'Division B',
            'assistant_id': self.employee.id,
            'estate_location': True,
            'estate_location_level': '2',
        })

        self.lha = self.env['estate_telegram.lha']

    def test_00_test(self):
        """ Init test"""
        self.assertTrue(self.user_assistant)
        self.assertTrue(self.division_a)
        return True

    def test_01_get_division(self):
        """ Get all division a user responsible to"""

        division_ids = self.lha.division(self.employee.id)
        self.assertTrue(division_ids)

        # assistant without division
        other_division_ids = self.lha.division(self.employee_b.id)
        self.assertFalse(other_division_ids)

        return True

    def test_02_get_activities(self):
        """ Get activities"""
        estate_id = self.employee.estate_id
        division_ids = self.lha.division(self.employee.id)

        for division in division_ids:
            data = {'form': {
                'date_start': '2017-10-01',
                'date_end': '2017-10-30',
                'estate_id': estate_id.ids,
                'division_id': division.ids
            }}
            self.lha.activities(data)

        return True

    def test_03_get_report(self):
        """ Return all activities within division."""
        self.assertTrue(self.lha.report(self.employee.id,1))
        self.assertFalse(self.lha.report())
        return True
