# -*- coding: utf-8 -*-
from openerp import api
from openerp.tests import TransactionCase
from openerp.exceptions import AccessError

class TestSecurity(TransactionCase):

    def setUp(self):
        super(TestSecurity, self).setUp()

        self.Ffb = self.env['estate.ffb']

        # User
        User = self.env['res.users'].with_context({'no_reset_password': True})
        group_user = self.ref('estate.group_user')
        group_assistant = self.ref('estate.group_assistant')
        group_ffb = self.ref('estate_ffb.group_ffb_user')

        self.user_no_access = User.create({
            'name': 'No Access', 'login': 'no-user', 'alias_name': 'no-user', 'email': 'no.user@user.com'})
        self.user_estate = User.create({
            'name': 'User', 'login': 'user', 'alias_name': 'user', 'email': 'user@user.com',
            'groups_id': [(6, 0, [group_user])]})
        self.user_assistant = User.create({
            'name': 'Assistant', 'login': 'assistant', 'alias_name': 'assistant', 'email': 'assistant@assistant.com',
            'groups_id': [(6, 0, [group_assistant])]})
        self.user_ffb = self.env.ref('estate_ffb.user_ffb')

        self.vals = {
            'estate_id': self.ref('estate.estate'),
            'division_id': self.ref('estate.division_1'),
            'date': '2017-01-01',
            'company_id': self.ref('base.main_company'),
            'clerk_id': self.ref('hr.employee_al'),
            'approver_id': self.ref('hr.employee_fp')
        }

    def test_00_no_access(self):
        """ Do not allow no groups create data."""
        with self.assertRaises(AccessError):
            self.Ffb.sudo(self.user_no_access).create(self.vals)

    def test_01_group_user(self):
        """ Do not allow estate user create data."""
        with self.assertRaises(AccessError):
            self.assertTrue(self.Ffb.sudo(self.user_estate).create(self.vals))

    def test_02_group_assistant(self):
        """ Allow estate assistant create data."""
        self.assertTrue(self.Ffb.sudo(self.user_assistant).create(self.vals))

    def test_03_group_ffb_user(self):
        """ Allow ffb user create data."""

        # check if create return true
        ffb_id = self.Ffb.sudo(self.user_ffb).create(self.vals)
        self.assertTrue(ffb_id)

        # check if able to open block template
        self.assertTrue(ffb_id.estate_id.usage)

        # check if unlink raised access error
        with self.assertRaises(AccessError):
            self.assertTrue(ffb_id.estate_id.unlink(), 'Danger! FFB user unlinked stock location')

        # check if read contract raised access error
        with self.assertRaises(AccessError):
            self.assertTrue(ffb_id.clerk_id.contract_id)
