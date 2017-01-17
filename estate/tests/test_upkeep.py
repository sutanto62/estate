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

        assistant_id = self.env.ref('hr.employee_al')
        team_id = self.env.ref('estate.team_syukur')
        estate_id = self.env.ref('stock.stock_main_estate')
        division_id = self.env.ref('stock.stock_division_1')

        wage_val = {
            'name': 'UMR Regional 2016',
            'active': True,
            'date_start': (datetime.today() - relativedelta.relativedelta(month=1,day=1)).strftime(DF),
            'estate_id': estate_id.id,
            'wage': 1875000,
            'number_of_days': 25,
            'overtime_amount': 10000,
        }

        self.Wage.create(wage_val)

        self.upkeep_val = {
            'name': 'BKM',
            'assistant_id': team_id.id,
            'team_id': assistant_id.id,
            'date': datetime.today().strftime(DF),
            'estate_id': estate_id.id,
            'division_id': division_id.id,
        }

    def test_00_check_date_00_today(self):
        config = self.env['estate.config.settings'].search([], limit=1)

        # I changed default max day to 3
        config['default_max_day'] = 0
        self.assertEqual(config['default_max_day'], 0, 'Estate: failed to get config value')
        self.upkeep_val['max_day'] = config['default_max_day']

        # I created upkeep record for today
        upkeep_today = self.Upkeep.create(self.upkeep_val)
        self.assertTrue(upkeep_today, 'Estate: failed to create upkeep record for today.')

    def test_00_check_date_01_week_late(self):
        """ Check upkeep date should not less than 3 days """
        config = self.env['estate.config.settings'].search([], limit=1)

        # I changed default max day to 3
        config['default_max_day'] = 3
        self.assertEqual(config['default_max_day'], 3, 'Estate: failed to get config value')

        # I created upkeep record for last week
        with self.assertRaises(ValidationError):
            self.upkeep_val['max_day'] = config['default_max_day']
            self.upkeep_val['date'] = (datetime.today() + relativedelta.relativedelta(weeks=-1)).strftime(DF)
            self.Upkeep.create(self.upkeep_val)

    def test_00_check_date_01_week_earlier(self):
        """ Check upkeep date should not greater than 3 days """
        config = self.env['estate.config.settings'].search([], limit=1)

        # I changed default max day to 3
        config['default_max_day'] = 3
        self.assertEqual(config['default_max_day'], 3, 'Estate: failed to get config value')

        # I created upkeep record for next week
        with self.assertRaises(ValidationError):
            self.upkeep_val['max_day'] = config['default_max_day']
            self.upkeep_val['date'] = (datetime.today() + relativedelta.relativedelta(weeks=1)).strftime(DF)
            self.Upkeep.create(self.upkeep_val)

    def test_01_check_activity_line(self):
        val = {
            'date': datetime.today().strftime(DF),
            'team_id': self.env.ref('estate.team_syukur').id,
            'assistant_id': self.env.ref('hr.employee_al').id,
            'division_id':self.env.ref('stock.stock_nursery').id,
            'activity_line_ids': [
                (0, 0, {
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'unit_amount': 20,
                }),
                (0, 0, {
                    'activity_id': self.env.ref('estate.activity_136').id,
                    'unit_amount': 10,
                }),
            ]
        }

        upkeep = self.Upkeep.create(val)
        self.assertTrue(upkeep, 'Estate: could not create upkeep')

        # Imitate activity more than once
        val_activity = {
            'activity_line_ids': [
                (0, 0, {
                    'activity_id': self.env.ref('estate.activity_136').id,
                    'unit_amount': 10,
                }),
            ]
        }
        with self.assertRaises(ValidationError):
            upkeep.write(val_activity)

        # Imitate sum labour quantity greater than unit_amount
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
            upkeep.write(val_labour)

    def test_02_check_labour_line(self):
        """ Check total quantity work result did  not exceed targeted quantity for single activity """
        val = {
            'date': datetime.today().strftime(DF),
            'team_id': self.env.ref('estate.team_syukur').id,
            'assistant_id': self.env.ref('hr.employee_al').id,
            'division_id': self.env.ref('stock.stock_nursery').id,
            'activity_line_ids': [
                (0, 0, {
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'unit_amount': 20,
                })
            ]
        }

        upkeep = self.Upkeep.create(val)

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
            upkeep.write(val_labour)

    def test_02_compute_activity_contract(self):
        # Imitate master data activity contract is True
        self.env.ref('estate.activity_135').write({'contract': True})

        val = {
            'date': datetime.today().strftime(DF),
            'team_id': self.env.ref('estate.team_syukur').id,
            'assistant_id': self.env.ref('hr.employee_al').id,
            'division_id': self.env.ref('stock.stock_nursery').id,
            'estate_id': self.env.ref('stock.stock_main_estate').id,
            'activity_line_ids': [
                (0, 0, {
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'contract': True,
                    'unit_amount': 20,
                })
            ],
            'labour_line_ids': [
                (0, 0, {
                    'employee_id': self.env.ref('estate.khl_5').id,
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'quantity': 15
                }),
                (0, 0, {
                    'employee_id': self.env.ref('estate.khl_4').id,
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'quantity': 5
                })
            ]
        }
        upkeep = self.Upkeep.create(val)

        self.assertTrue(upkeep)
        # self.assertTrue(upkeep.labour_line_ids[0].activity_contract, 'Estate: _compute_activity_contract failed')

    # Define division by team instead of assistant.
    # def test_00_onchange_assistant_division(self):
    #     self.env.ref('estate.block_1').write({'assistant_id': self.env.ref('hr.employee_al').id})
    #     val = {
    #         'date': datetime.today().strftime(DF),
    #         'team_id': self.env.ref('estate.team_syukur').id,
    #         'assistant_id': self.env.ref('hr.employee_al').id,
    #         'division_id': self.env.ref('stock.stock_nursery').id,
    #     }
    #     upkeep = self.Upkeep.create(val)
    #
    #     # Imitate onchange assistant event
    #     # upkeep._onchange_assistant_id()
    #     # self.assertEqual(upkeep['division_id']['name'], 'Division 1', 'Estate: _onchange_assistant_id is failed')
    #
    #     # Imitate onchange division event
    #     upkeep._onchange_division_id()
    #     self.assertEqual(upkeep['estate_id']['name'], 'LYD', 'Estate: _onchange_division_id is failed')