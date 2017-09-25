# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError

class TestActivity(TransactionCase):

    def setUp(self):
        super(TestActivity, self).setUp()
        self.Activity = self.env['estate.activity']

        # Setup user
        User = self.env['res.users'].with_context({'no_reset_password': True})
        (group_admin, group_estate, group_agronomy) = (self.ref('base.group_no_one'),
                                                       self.ref('estate.group_user'),
                                                       self.ref('estate.group_agronomi'))
        self.user_admin = User.create({
            'name': 'Lukas Peeters', 'login': 'Lukas', 'alias_name': 'lukas', 'email': 'lukas.petters@example.com',
            'groups_id': [(6, 0, [group_admin, group_estate])]})
        self.user_estate = User.create({
            'name': 'Wout Janssens', 'login': 'Wout', 'alias_name': 'wout', 'email': 'wout.janssens@example.com',
            'groups_id': [(6, 0, [group_estate])]})
        self.user_agronomy = User.create({
            'name': 'Broot Janssens', 'login': 'Broot', 'alias_name': 'broott', 'email': 'broot.janssens@example.com',
            'groups_id': [(6, 0, [group_agronomy])]})

        self.vals = {
            'name': 'Activity',
            'type': 'normal',
            'qty_base': 7.5,
            'qty_base_min': 5,
            'qty_base_max': 10,
            'ratio_min': 0,
            'ratio_max': 0,
        }

    def test_00_onchange_productivity(self):
        """ Create base activity"""

        # I created activity
        activity_id = self.Activity.sudo(self.user_agronomy).create(self.vals)
        self.assertTrue(activity_id, 'Agronomy user cannot create activity.')

    def test_01_create_activity_productivity(self):
        """ Create three type activity productivity: reference, smaller, bigger."""

        a = {
            'name': 'Reference',
            'type': 'normal',
            'qty_base': 7.5,
            'qty_base_min': 5,
            'qty_base_max': 10,
            'ratio_min': 0,
            'ratio_max': 0,
            'is_productivity': True,
            'productivity': 'reference',
            'factor': 1.0
        }

        b = {
            'name': 'Smaller',
            'type': 'normal',
            'qty_base': 7.5,
            'qty_base_min': 5,
            'qty_base_max': 10,
            'ratio_min': 0,
            'ratio_max': 0,
            'is_productivity': True,
            'productivity': 'smaller',
            'factor': 100.0
        }
        c= {
            'name': 'Bigger',
            'type': 'normal',
            'qty_base': 7.5,
            'qty_base_min': 5,
            'qty_base_max': 10,
            'ratio_min': 0,
            'ratio_max': 0,
            'is_productivity': True,
            'productivity': 'bigger',
            'factor': 1000.0
        }

        activity_obj = self.env['estate.activity']

        activity_reference = activity_obj.create(a)
        self.assertTrue(activity_reference)
        self.assertEqual(activity_reference.factor_inv, 1.0)
        self.assertEqual(activity_reference.convert_quantity(100), 100.0)
        self.assertEqual(activity_reference.convert_quantity(0), 0.0)

        activity_smaller = activity_obj.create(b)
        self.assertTrue(activity_smaller)
        self.assertEqual(activity_smaller.factor_inv, 0.01)
        self.assertEqual(activity_smaller.convert_quantity(100), 1.0)
        self.assertEqual(activity_smaller.convert_quantity(0), 0.0)

        activity_bigger = activity_obj.create(c)
        self.assertTrue(activity_bigger)
        self.assertEqual(activity_bigger.factor_inv, 0.001)
        self.assertEqual(activity_bigger.convert_quantity(1000), 1.0)

        # negative number
        self.assertEqual(activity_bigger.convert_quantity(-0.1), 0.0)
        self.assertEqual(activity_bigger.convert_quantity('a'), 0.0)


