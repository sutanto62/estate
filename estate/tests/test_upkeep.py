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

        self.upkeep_val = {
            'name': 'BKM',
            'assistant_id': team_id.id,
            'team_id': assistant_id.id,
            'date': datetime.today().strftime(DF),
            'estate_id': estate_id.id,
            'division_id': division_id.id,
        }

    def test_check_date_00_today(self):
        config_val = {
            'default_max_entry_day': 3
        }

        # Imitate config
        config = self.Config.create(config_val)
        self.assertEqual(config['default_max_entry_day'], 3, 'Estate: failed to get config value')

        # Imitate creating upkeep today
        upkeep = self.Upkeep.create(self.upkeep_val)
        self.assertTrue(upkeep, 'Estate: failed to create upkeep record for today.')
        upkeep.unlink()

    def test_check_date_01_week_late(self):
        """ Check upkeep date should not less than 3 days """
        config_val = {
            'default_max_entry_day': 3
        }

        # Imitate config
        config = self.Config.create(config_val)
        self.assertEqual(config['default_max_entry_day'], 3, 'Estate: failed to get config value')

        # Imitate creating last week upkeep
        with self.assertRaises(ValidationError):
            self.upkeep_val['date'] = (datetime.today() + relativedelta.relativedelta(weeks=-1)).strftime(DF)
            self.Upkeep.create(self.upkeep_val)

    def test_check_date_01_week_earlier(self):
        """ Check upkeep date should not greater than 3 days """
        config_val = {
            'default_max_entry_day': 3
        }

        # Imitate config
        config = self.Config.create(config_val)
        self.assertEqual(config['default_max_entry_day'], 3, 'Estate: failed to get config value')

        # Imitate creating last week upkeep
        with self.assertRaises(ValidationError):
            self.upkeep_val['date'] = (datetime.today() + relativedelta.relativedelta(weeks=1)).strftime(DF)
            self.Upkeep.create(self.upkeep_val)

    # def test_get_labour_activity(self):
    #     upkeep = self.demo
    #     for activity in upkeep.get_labour_activity():
    #         self.assertTrue(activity, 'Estate: failed to get labour activity')

    def test_check_activity_line(self):
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
                    'employee_id': self.env.ref('hr_employee.khl_5').id,
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'quantity': 20
                }),
                (0, 0, {
                    'employee_id': self.env.ref('hr_employee.khl_4').id,
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'quantity': 20
                })
            ]
        }
        with self.assertRaises(ValidationError):
            upkeep.write(val_labour)

    def test_check_labour_line(self):
        """ Check total quantity work result did  not exceed targeted quantity for single activity """
        upkeep = self.demo

        # Create labour exceed upkeep activity quantity
        val = {
            'upkeep_id': self.env.ref('estate.estate_upkeep_2').id,
            'employee_id': self.env.ref('hr_employee.khl_5').id,
            'activity_id': self.env.ref('estate.activity_134').id,
            'location_id': self.env.ref('estate.block_2').id,
            'attendance_code_id': self.env.ref('estate.hr_attendance_k').id,
            'quantity': 20
        }
        upkeep.labour_line_ids.write(val)

        # 20 < 15.5
        with self.assertRaises(ValidationError):
            upkeep._check_labour_line()

    def test_compute_upkeep_name(self):
        self.assertTrue(self.demo['name'], 'Estate: compute_upkeep_name return false')

    def test_onchange_assistant_division(self):
        self.env.ref('estate.block_1').write({'assistant_id': self.env.ref('hr.employee_al').id})
        val = {
            'date': datetime.today().strftime(DF),
            'team_id': self.env.ref('estate.team_syukur').id,
            'assistant_id': self.env.ref('hr.employee_al').id,
            'division_id':self.env.ref('stock.stock_nursery').id,
        }
        upkeep = self.Upkeep.create(val)

        # Imitate onchange assistant event
        upkeep._onchange_assistant_id()
        self.assertEqual(upkeep['division_id']['name'], 'Division 1', 'Estate: _onchange_assistant_id is failed')

        # Imitate onchange division event
        upkeep._onchange_division_id()
        self.assertEqual(upkeep['estate_id']['name'], 'LYD', 'Estate: _onchange_division_id is failed')# -*- coding: utf-8 -*-

    # def test_02_compute_wage_overtime(self):