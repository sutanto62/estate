# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from openerp.addons.hr_payroll import hr_payroll
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError

class TestUpkeep(TransactionCase):

    def setUp(self):
        super(TestUpkeep, self).setUp()
        self.Wage = self.env['estate.wage']
        self.Upkeep = self.env['estate.upkeep']
        self.Activity = self.env['estate.upkeep.activity']
        self.Labour = self.env['estate.upkeep.labour']
        self.Material = self.env['estate.upkeep.material']
        self.Config = self.env['estate.config.settings']

        self.demo = self.env.ref('estate.estate_upkeep_2')

        self.assistant_id = self.env.ref('hr.employee_al')
        self.team_id = self.env.ref('estate.team_syukur')
        self.estate_id = self.env.ref('stock.stock_main_estate')
        self.division_id = self.env.ref('stock.stock_division_1')
        self.att_code_k = self.env.ref('estate.hr_attendance_k')
        self.att_code_l = self.env.ref('estate.hr_attendance_k2')
        self.product_sp = self.env.ref('estate.product_product_sp')

        # Setup user
        User = self.env['res.users'].with_context({'no_reset_password': True})
        (group_admin, group_estate) = (self.ref('base.group_no_one'), self.ref('estate.group_user'))
        self.user_admin = User.create({
            'name': 'Lukas Peeters', 'login': 'Lukas', 'alias_name': 'lukas', 'email': 'lukas.petters@example.com',
            'groups_id': [(6, 0, [group_admin, group_estate])]})
        self.user_estate = User.create({
            'name': 'Wout Janssens', 'login': 'Wout', 'alias_name': 'wout', 'email': 'wout.janssens@example.com',
            'groups_id': [(6, 0, [group_estate])]})

        wage_val = {
            'name': 'UMR Regional 2016',
            'active': True,
            'date_start': (datetime.today() - relativedelta.relativedelta(month=1,day=1)).strftime(DF),
            'estate_id': self.estate_id.id,
            'wage': 1875000,
            'number_of_days': 25,
            'overtime_amount': 10000,
        }

        self.Wage.create(wage_val)

        self.upkeep_val = {
            'name': 'BKM',
            'assistant_id': self.team_id.id,
            'team_id': self.assistant_id.id,
            'date': datetime.today().strftime(DF),
            'estate_id': self.estate_id.id,
            'division_id': self.division_id.id,
        }

        self.upkeep = {
            'name': 'BKM',
            'assistant_id': self.team_id.id,
            'team_id': self.assistant_id.id,
            'date': datetime.today().strftime(DF),
            'estate_id': self.estate_id.id,
            'division_id': self.division_id.id,
            'activity_line_ids': [
                (0, 0, {
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'unit_amount': 20,
                })
            ],
            'labour_line_ids': [
                (0, 0, {
                    'employee_id': self.env.ref('estate.khl_5').id,
                    'attendance_code_id': self.att_code_k.id,
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'quantity': 10
                }),
                (0, 0, {
                    'employee_id': self.env.ref('estate.khl_4').id,
                    'attendance_code_id': self.att_code_k.id,
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'quantity': 10
                })
            ]
        }

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

        self.upkeep_id = self.Upkeep.sudo(self.estate_user).create(self.upkeep)

    def test_00_create_upkeep(self):
        """ Check upkeep created."""
        self.assertTrue(self.upkeep_id, 'Estate user could not create upkeep')

    def test_01_check_date_00_today(self):
        """ Check default maximum day config."""

        config = self.env['estate.config.settings'].search([], limit=1)

        # I changed default max day to 0
        config['default_max_day'] = 0
        self.assertEqual(config['default_max_day'], 0, 'Estate: failed to get config value')
        self.upkeep_id['max_day'] = config['default_max_day']

        # I created upkeep record for today
        self.assertTrue(self.upkeep_id, 'Estate: failed to create upkeep record for today.')

        # Check if validation error occur
        next_week_date = (datetime.today() + relativedelta.relativedelta(days=1)).strftime(DF),
        with self.assertRaises(ValidationError):
            self.upkeep_id.write({'date': next_week_date})

    def test_02_check_activity_line(self):
        """ Check validation for upkeep activity."""

        # Check if duplicate activities raised validation error
        val_activity = {
            'activity_line_ids': [
                (0, 0, {
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'unit_amount': 10,
                }),
            ]
        }
        with self.assertRaises(ValidationError):
            self.upkeep_id.write(val_activity)

        # Check if sum labour quantity greater than unit_amount raised validation error
        val_labour = {
            'labour_line_ids': [
                (0, 0, {
                    'employee_id': self.env.ref('estate.khl_5').id,
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'quantity': 20
                }),
                (0, 0, {
                    'employee_id': self.env.ref('estate.khl_4').id,
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'quantity': 20
                })
            ]
        }

        with self.assertRaises(ValidationError):
            self.upkeep_id.write(val_labour)

    def test_03_check_labour_line(self):
        """ Check upkeep labor validation."""

        # Imitate sum labour quantity greater than unit_amount
        val_labour = {
            'labour_line_ids': [
                (0, 0, {
                    'employee_id': self.env.ref('estate.khl_5').id,
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'quantity': 15
                }),
                (0, 0, {
                    'employee_id': self.env.ref('estate.khl_4').id,
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'quantity': 15
                })
            ]
        }

        with self.assertRaises(ValidationError):
            self.upkeep_id.write(val_labour)

    # def test_04_compute_total_labour(self):
    #     """ Compute total labour in single upkeep."""
    #
    #     # I created upkeep with single activity and two labours
    #     upkeep = self.Upkeep.create(self.upkeep)
    #     for labour in upkeep.labour_line_ids:
    #         labour._compute_number_of_day()
    #     upkeep._compute_total_labour_line()
    #
    #     self.assertEqual(upkeep.total_labour, 2, 'Upkeep: total labour was not 2.')
    #     self.assertEqual(upkeep.total_number_of_day, 2, 'Upkeep: total number of day was not 2.')
    #     self.assertEqual(upkeep.total_overtime, 0, 'Upkeep: total number of day was not 0.')
    #     self.assertEqual(upkeep.total_piece_rate, 0, 'Upkeep: total number of day was not 0.')
    #
    #     # I edit upkeep with more activity and two labours works at these activities
    #     val = {
    #         'activity_line_ids': [
    #             (0, 0, {
    #                 'activity_id': self.env.ref('estate.activity_136').id,
    #                 'unit_amount': 20,
    #             })
    #         ],
    #         'labour_line_ids': [
    #             (0, 0, {
    #                 'employee_id': self.env.ref('estate.khl_5').id,
    #                 'activity_id': self.env.ref('estate.activity_136').id,
    #                 'quantity': 10
    #             }),
    #             (0, 0, {
    #                 'employee_id': self.env.ref('estate.khl_4').id,
    #                 'activity_id': self.env.ref('estate.activity_136').id,
    #                 'quantity': 10
    #             })
    #         ]
    #     }
    #
    #     upkeep.write(val)
    #     upkeep._compute_total_labour_line()
    #     self.assertEqual(upkeep.total_labour, 2, 'Total labour returned value is not 2')
    #
    def test_05_confirm_approve_draft_upkeep(self):
        """ Check action button."""

        # It should be in draft state
        self.assertEqual(self.upkeep_id.state, 'draft')

        # I pressed confirm button
        self.upkeep_id.button_confirmed()
        self.assertEqual(self.upkeep_id.state, 'confirmed')

        # I pressed approve button
        self.upkeep_id.button_approved()
        self.assertEqual(self.upkeep_id.state, 'approved')

        # I pressed draft button as normal user
        with self.assertRaises(ValidationError):
            self.upkeep_id.sudo(self.estate_user).draft_selected()

        # checked if only user agronomy able to redraft
        with self.assertRaises(ValidationError):
            self.upkeep_id.sudo(self.estate_user).draft_selected()

        # checked if user agronomy able to redraft or not
        self.upkeep_id.sudo(self.estate_agronomy).draft_selected()
        self.assertEqual(self.upkeep_id.state, 'draft')

        # checked if each labor line state went draft or not
        for labour in self.upkeep_id.labour_line_ids:
            self.assertEqual(labour.state, 'draft')

        # checked if each material line state went draft or not
        for material in self.upkeep_id.material_line_ids:
            self.assertEqual(material.state, 'draft')

