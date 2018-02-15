# -*- coding: utf-8 -*-
from openerp import api
from openerp.tests import TransactionCase
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError, AccessError

class TestSecurity(TransactionCase):

    def setUp(self):
        super(TestSecurity, self).setUp()

        self.MaterialOrder = self.env['estate_stock.material_order']

        # User
        User = self.env['res.users'].with_context({'no_reset_password': True})
        group_stock_user = self.ref('stock.group_stock_user')
        group_stock_assistant = self.ref('stock.group_stock_assistant')
        group_stock_manager = self.ref('stock.group_stock_manager')

        self.user_no_access = User.create({
            'name': 'No Access', 'login': 'no-user', 'alias_name': 'no-user', 'email': 'no.user@user.com'})
        self.user_stock_user = User.create({
            'name': 'User', 'login': 'user', 'alias_name': 'user', 'email': 'user@user.com',
            'groups_id': [(6, 0, [group_stock_user])]})
        self.user_stock_assistant = User.create({
            'name': 'Assistant', 'login': 'assistant', 'alias_name': 'assistant', 'email': 'assistant@assistant.com',
            'groups_id': [(6, 0, [group_stock_assistant])]})
        self.user_stock_manager = User.create({
            'name': 'Manager', 'login': 'manager', 'alias_name': 'manager', 'email': 'manager@manager.com',
            'groups_id': [(6, 0, [group_stock_manager])]})

        self.vals = {
            'estate_id': self.ref('estate.estate'),
            'division_id': self.ref('estate.division_1'),
            'date_expected': '2017-01-01',
            'move_type': 'one',
            'picking_type_id': self.ref('stock.picking_type_internal')
        }

    def test_00_no_access(self):
        """ Do not allow no groups create data."""
        with self.assertRaises(AccessError):
            self.MaterialOrder.sudo(self.user_no_access).create(self.vals)

    def test_01_stock_user(self):
        self.assertTrue(self.MaterialOrder.sudo(self.user_stock_user).create(self.vals))

    def test_02_stock_assistant(self):
        self.assertTrue(self.MaterialOrder.sudo(self.user_stock_assistant).create(self.vals))

    def test_03_stock_manager(self):
        self.assertTrue(self.MaterialOrder.sudo(self.user_stock_manager).create(self.vals))
