# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
import datetime
from dateutil import relativedelta
from openerp.exceptions import AccessError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from hr_fingerprint_ams import *


class TestSecurity(TransactionCase):

    def setUp(self):
        super(TestSecurity, self).setUp()

        # Object
        self.Activity = self.env['estate.activity']

        # User
        User = self.env['res.users'].with_context({'no_reset_password': True})
        group_user = self.ref('estate.group_user')
        group_assistant = self.ref('estate.group_assistant')
        group_manager = self.ref('estate.group_manager')
        group_agronomy = self.ref('estate.group_agronomi')

        self.estate_user = User.create({
            'name': 'Irma', 'login': 'irma', 'alias_name': 'irma', 'email': 'irma@irma.com',
            'groups_id': [(6, 0, [group_user])]})
        self.estate_assistant = User.create({
            'name': 'Intan', 'login': 'intan', 'alias_name': 'intan', 'email': 'intan@intan.com',
            'groups_id': [(6, 0, [group_assistant])]})
        self.estate_manager = User.create({
            'name': 'Agus', 'login': 'agus', 'alias_name': 'agus', 'email': 'agus@agus.com',
            'groups_id': [(6, 0, [group_manager])]})
        self.estate_agronomy = User.create({
            'name': 'Cahyo', 'login': 'cahyo', 'alias_name': 'cahyo', 'email': 'cayho@cahyo.com',
            'groups_id': [(6, 0, [group_agronomy])]})

    def test_01_create_estate_activity(self):
        """ Only estate agronomy allowed to create/edit estate activity."""

        val = {
            'name': 'Activity',
            'type': 'normal',
            'qty_base': 1,
        }

        # User try to create estate activity
        with self.assertRaises(AccessError):
            activity_id = self.Activity.sudo(self.estate_user).create(val)

        # Assistant try to create estate activity
        with self.assertRaises(AccessError):
            activity_id = self.Activity.sudo(self.estate_assistant).create(val)

        # Manager try to create estate activity
        with self.assertRaises(AccessError):
            activity_id = self.Activity.sudo(self.estate_manager).create(val)

        # Agronomy created estate activity
        activity_id = self.Activity.sudo(self.estate_agronomy).create(val)
        self.assertTrue(activity_id, 'Agronomy should be able to create estate activity.')

        # User updated estate activity - upkeep require user has write access
        # with self.assertRaises(AccessError):
        #     activity_id.sudo(self.estate_user).update({'qty_base': 2})