# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
# from openerp.addons.hr_payroll import hr_payroll
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError


class TestUpkeep(TransactionCase):

    def setUp(self):
        super(TestUpkeep, self).setUp()

        self.EstateAttendance = self.env['estate.hr.attendance']
        self.Wage = self.env['estate.wage']
        self.Upkeep = self.env['estate.upkeep']
        self.Activity = self.env['estate.activity']
        self.UpkeepActivity = self.env['estate.upkeep.activity']
        self.Labour = self.env['estate.upkeep.labour']
        self.Material = self.env['estate.upkeep.material']
        self.Config = self.env['estate.config.settings']

        # setup location
        estate_id = self.env['estate.block.template'].sudo().create({
            'name': 'Estate',
            # 'inherit_location_id': stock_estate_id.id,
            'estate_location': True,
            'estate_location_level': '1',
            'estate_location_type': 'planted'
        })
        division_id = self.env['estate.block.template'].sudo().create({
            'name': 'Division',
            # 'inherit_location_id': stock_division_id.id,
            'estate_location': True,
            'estate_location_level': '2',
            'estate_location_type': 'planted'
        })
        block_a = self.env['estate.block.template'].sudo().create({
            'name': 'Blok A',
            # 'inherit_location_id': stock_block_a.id,
            'estate_location': True,
            'estate_location_level': '3',
            'estate_location_type': 'planted'
        })
        block_b = self.env['estate.block.template'].sudo().create({
            'name': 'Blok B',
            # 'inherit_location_id': stock_block_b.id,
            'estate_location': True,
            'estate_location_level': '3',
            'estate_location_type': 'planted'
        })

        # setup assistant, labor, estate team
        assistant_id = self.env['hr.employee'].sudo().create({
            'name': 'Assistant'
        })
        labor_a = self.env['hr.employee'].sudo().create({
            'name': 'Labor A',
            'contract_type': '2',
            'contract_period': '2'
        })
        self.labor_b = self.env['hr.employee'].sudo().create({
            'name': 'Labor B',
            'contract_type': '2',
            'contract_period': '2'
        })
        self.estate_contract_type_id = self.env['hr.contract.type'].sudo().create({
            'name': 'Estate Worker'
        })
        contract_b = self.env['hr.contract'].sudo().create({
            'name': 'Labor B Contract',
            'employee_id': self.labor_b.id,
            'wage': 3100000,
            'date_start': (datetime.today() + relativedelta.relativedelta(month=1, day=1)).strftime(DF),
            'date_end': (datetime.today() + relativedelta.relativedelta(years=1, month=1, days=-1)).strftime(DF),
            'type_id': self.estate_contract_type_id.id
        })
        team_id = self.env['estate.hr.team'].sudo().create({
            'name': 'Team',
            'date_effective': (datetime.today() + relativedelta.relativedelta(month=1, day=1)).strftime(DF),
            'employee_id': assistant_id.id,
            'member_ids': [
                (0, 0, {
                    'employee_id': labor_a.id
                }),
                (0, 0, {
                    'employee_id': self.labor_b.id
                })
            ]
        })

        # minimum regional wage
        wage_id = self.Wage.sudo().create({
            'name': 'UMR Regional 2016',
            'active': True,
            'date_start': (datetime.today() - relativedelta.relativedelta(month=1, day=1)).strftime(DF),
            'estate_id': estate_id.inherit_location_id.id,
            'wage': 1875000,
            'number_of_days': 25,
            'overtime_amount': 10000,
        })

        # attendance code
        attendance_k_id = self.EstateAttendance.sudo().create({
            'name': '1 Day Work',
            'code': 'K',
            'qty_ratio': 1.0,
            'unit_amount': 7.0
        })

        attendance_l_id = self.EstateAttendance.sudo().create({
            'name': '0.5 Day Work',
            'code': 'L',
            'qty_ratio': 0.5,
            'unit_amount': 3.5
        })

        activity_a = self.Activity.sudo().create({
            'name': 'Activity A',
            'type': 'normal',
            'qty_base': 200,
            'standard_price': 10,
            'piece_rate_price': 8,
            'activity_type': 'estate',
            'wage_method': 'standard'
        })

        activity_b = self.Activity.sudo().create({
            'name': 'Activity B',
            'type': 'normal',
            'qty_base': 100,
            'standard_price': 10,
            'piece_rate_price': 8,
            'activity_type': 'estate',
            'wage_method': 'standard'
        })

        # create upkeep
        self.upkeep = self.Upkeep.sudo().create({
            'date': datetime.today().strftime(DF),
            'team_id': team_id.id,
            'assistant_id': assistant_id.id,
            'division_id': division_id.inherit_location_id.id,
            'estate_id': estate_id.inherit_location_id.id,
            'activity_line_ids': [
                (0, 0, {
                    'activity_id': activity_a.id,
                    'unit_amount': 300,
                }),
                (0, 0, {
                    'activity_id': activity_b.id,
                    'unit_amount': 10,
                }),
            ],
            'labour_line_ids': [
                (0, 0, {
                    'employee_id': labor_a.id,
                    'activity_id': activity_a.id,
                    'attendance_code_id': attendance_k_id.id,
                    'quantity': 200
                }),
                (0, 0, {
                    'employee_id': self.labor_b.id,
                    'activity_id': activity_a.id,
                    'attendance_code_id': attendance_l_id.id,
                    'quantity': 100
                }),
            ]
        })

    def test_00_start(self):
        """ test"""
        self.assertTrue(self.upkeep)

    def test_01_compute_wage_number_of_day(self):
        """ Checked wage number of day."""

        # computed wage based on minimum regional wage
        self.upkeep.labour_line_ids[0]._compute_wage_number_of_day()
        self.assertEqual(self.upkeep.labour_line_ids[0].wage_number_of_day, 75000)

        # computed wage based on single contract
        self.upkeep.labour_line_ids[1]._compute_wage_number_of_day()
        self.assertEqual(self.upkeep.labour_line_ids[1].wage_number_of_day, 62000)

        # computed wage based on multiple contract, overlapped.
        self.env['hr.contract'].sudo().create({
            'name': 'Labor B Contract 2',
            'employee_id': self.labor_b.id,
            'wage': 6200000,
            'date_start': (datetime.today() + relativedelta.relativedelta(month=12, day=1)).strftime(DF),
            'date_end': (datetime.today() + relativedelta.relativedelta(years=1, month=1, days=-1)).strftime(DF),
            'type_id': self.estate_contract_type_id.id
        })
        self.upkeep.labour_line_ids[1]._compute_wage_number_of_day()
        self.assertEqual(self.upkeep.labour_line_ids[1].wage_number_of_day, 124000)

        # computed wage based on past due contract
        contract_b_second = self.env['hr.contract'].sudo().create({
            'name': 'Labor B Contract 3',
            'employee_id': self.labor_b.id,
            'wage': 3100000,
            'date_start': (datetime.today() + relativedelta.relativedelta(month=1, day=1)).strftime(DF),
            'date_end': (datetime.today() + relativedelta.relativedelta(month=3, days=-1)).strftime(DF),
            'type_id': self.estate_contract_type_id.id
        })
        self.upkeep.labour_line_ids[1]._compute_wage_number_of_day()
        self.assertEqual(self.upkeep.labour_line_ids[1].wage_number_of_day, 124000)
