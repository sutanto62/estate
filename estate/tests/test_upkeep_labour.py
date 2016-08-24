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

        # self.demo = self.env.ref('estate.estate_upkeep_2')

        assistant_id = self.env.ref('hr.employee_al')
        team_id = self.env.ref('estate.team_syukur')
        estate_id = self.env.ref('stock.stock_main_estate')
        division_id = self.env.ref('stock.stock_division_1')

        wage_val = {
            'name': 'UMR Regional 2016',
            'active': True,
            'date_start': (datetime.today() - relativedelta.relativedelta(month=1, day=1)).strftime(DF),
            'estate_id': estate_id.id,
            'wage': 1875000,
            'number_of_days': 25,
            'overtime_amount': 10000,
        }

        self.Wage.create(wage_val)

        val = {
            'date': datetime.today().strftime(DF),
            'team_id': self.env.ref('estate.team_syukur').id,
            'assistant_id': self.env.ref('hr.employee_al').id,
            'division_id': self.env.ref('stock.stock_nursery').id,
            'estate_id': self.env.ref('stock.stock_main_estate').id,
            'activity_line_ids': [
                (0, 0, {
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'unit_amount': 20,
                }),
                (0, 0, {
                    'activity_id': self.env.ref('estate.activity_136').id,
                    'unit_amount': 10,
                }),
            ],
            'labour_line_ids': [
                (0, 0, {
                    'employee_id': self.env.ref('hr_employee.khl_5').id,
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'attendance_code_id': self.env.ref('estate.hr_attendance_k').id,
                    'quantity': 15
                }),
                (0, 0, {
                    'employee_id': self.env.ref('hr_employee.khl_4').id,
                    'activity_id': self.env.ref('estate.activity_135').id,
                    'attendance_code_id': self.env.ref('estate.hr_attendance_k2').id,
                    'quantity': 5
                }),
            ]
        }

        self.upkeep = self.Upkeep.create(val)

    def test_00_new_upkeep(self):
        """ Create new upkeep entry, single activity many labour """
        self.assertTrue(self.upkeep)

    def test_01_attendance_code(self):
        """ Labour activity attendance K and K2 """
        for labour in self.upkeep.labour_line_ids.sorted(key=lambda r: r.employee_id):
            labour._compute_number_of_day()

        self.assertEqual(self.upkeep.labour_line_ids[0].number_of_day, 0.5)
        self.assertEqual(self.upkeep.labour_line_ids[1].number_of_day, 1.0)

    def test_01_compute_number_of_day(self):
        """ Compute number of day for attendance, standard (and contract) based activity """
        activity = self.env.ref('estate.activity_135')

        # Imitate attendance wage method and labour activity quantity minimum
        for labour in self.upkeep.labour_line_ids.sorted(key=lambda r: r.employee_id):
            labour._compute_number_of_day()
        self.assertEqual(self.upkeep.labour_line_ids[0].number_of_day, 0.5, 'Estate: _compute_number_of_day for attendance based activity failed')
        self.assertEqual(self.upkeep.labour_line_ids[1].number_of_day, 1.0, 'Estate: _compute_number_of_day for attendance based activity failed')

        # Imitate standard quantity wage method and labour activity below minimum ( < K2)
        activity.write({'wage_method': 'standard'})
        for labour in self.upkeep.labour_line_ids.sorted(key=lambda r: r.employee_id):
            labour.write({'quantity': 1})
            labour._compute_number_of_day()
        self.assertEqual(self.upkeep.labour_line_ids[0].number_of_day, 0, 'Estate: _compute_number_of_day for standard based activity failed')
        self.assertEqual(self.upkeep.labour_line_ids[1].number_of_day, 0, 'Estate: _compute_number_of_day for standard based activity failed')

        # Imitate contract based
        activity.write({'contract': True})  # Contract should be standard quantity wage.
        for labour in self.upkeep.labour_line_ids.sorted(key=lambda r: r.employee_id):
            labour._compute_number_of_day()
        self.assertEqual(self.upkeep.labour_line_ids[0].number_of_day, 0, 'Estate: _compute_number_of_day for contract based activity failed')

