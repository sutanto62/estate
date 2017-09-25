# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError

class TestEstateUpkeep(TransactionCase):

    def setUp(self):
        super(TestEstateUpkeep, self).setUp()

        # self.Account = self.env['account.account']
        # self.UpkeepLaboself.Upkeep = self.env['estate.upkeep']
        self.Upkeep = self.env['estate.upkeep']
        self.Activity = self.env['estate.upkeep.activity']
        self.Labour = self.env['estate.upkeep.labour']
        self.Material = self.env['estate.upkeep.material']
        self.Config = self.env['estate.config.settings']

        self.assistant_id = self.env.ref('hr.employee_al')
        self.team_id = self.env.ref('estate.team_syukur')
        self.estate_id = self.env.ref('stock.stock_main_estate')
        self.division_id = self.env.ref('stock.stock_division_1')
        self.att_code_k = self.env.ref('estate.hr_attendance_k')
        self.att_code_l = self.env.ref('estate.hr_attendance_k2')
        self.product_sp = self.env.ref('estate.product_product_sp')

        User = self.env['res.users'].with_context({'no_reset_password': True})
        group_user = self.ref('estate.group_user')
        group_assistant = self.ref('estate.group_assistant')
        group_manager = self.ref('estate.group_manager')
        group_agronomy = self.ref('estate.group_agronomi')

        self.estate_user = User.create({
            'name': 'Irma', 'login': 'irma', 'alias_name': 'irma', 'email': 'irma@irma.com',
            'groups_id': [(6, 0, [group_user])]})

        # assign planted year
        self.tt_2018 = self.env.ref('.estate_planted_year_2018')
        self.block_1 = self.env.ref('estate.block_1').write({'planted_year_id': self.tt_2018.id})
        self.block_2 = self.env.ref('estate.block_2').write({'planted_year_id': self.tt_2018.id})

        # assign account
        self.env.ref('estate.activity_54110_3').write({'general_account_id': self.env.ref('.coa_hja_54110').id})
        self.env.ref('estate.activity_54110_5').write({'general_account_id': self.env.ref('.coa_hja_54110').id})

        # create upkeep with multiple activity within single account
        self.vals = {
            'name': 'BKM',
            'assistant_id': self.team_id.id,
            'team_id': self.assistant_id.id,
            'date': datetime.today().strftime(DF),
            'company_id': self.env.ref('base.main_company').id,
            'estate_id': self.estate_id.id,
            'division_id': self.division_id.id,
            'state': 'approved',
            'activity_line_ids': [
                (0, 0, {
                    'activity_id': self.env.ref('estate.activity_54110_3').id,
                    'unit_amount': 10
                }),
                (0, 0, {
                    'activity_id': self.env.ref('estate.activity_54110_5').id,
                    'unit_amount': 15
                })
            ],
            'labour_line_ids': [
                (0, 0, {
                    'employee_id': self.env.ref('estate.khl_5').id,
                    'attendance_code_id': self.att_code_k.id,
                    'activity_id': self.env.ref('estate.activity_54110_3').id,
                    'quantity': 10,
                    'location_id': self.env.ref('estate.block_1').id
                }),
                (0, 0, {
                    'employee_id': self.env.ref('estate.khl_4').id,
                    'attendance_code_id': self.att_code_k.id,
                    'activity_id': self.env.ref('estate.activity_54110_5').id,
                    'quantity': 15,
                    'location_id': self.env.ref('estate.block_2').id
                })
            ]
        }

    def test_00_get_quantity(self):
        """ Get quantity account productivity."""
        # imitate param
        start = (datetime.today() + relativedelta.relativedelta(day=1)).strftime(DF)
        end = (datetime.today() + relativedelta.relativedelta(months=1, day=1, days=-1)).strftime(DF)
        analytic = self.tt_2018.id
        account = self.env.ref('.coa_hja_54110').id
        company = self.env.ref('base.main_company').id

        # account productivity from single upkeep
        upkeep_id = self.Upkeep.sudo(self.estate_user).create(self.vals)
        self.assertTrue(upkeep_id, 'Estate user could not create upkeep.')
        self.assertEqual(self.Labour.get_quantity(start, end, analytic, account, company)['quantity'], 15)

        vals = {
            'assistant_id': self.team_id.id,
            'team_id': self.assistant_id.id,
            'date' : (datetime.today() + relativedelta.relativedelta(days=1)).strftime(DF),
            'company_id': self.env.ref('base.main_company').id,
            'estate_id': self.estate_id.id,
            'division_id': self.division_id.id,
            'state': 'approved',
            'activity_line_ids': [
                (0, 0, {
                    'activity_id': self.env.ref('estate.activity_54110_3').id,
                    'unit_amount': 10
                }),
                (0, 0, {
                    'activity_id': self.env.ref('estate.activity_54110_5').id,
                    'unit_amount': 15
                })
            ],
            'labour_line_ids': [
                (0, 0, {
                    'employee_id': self.env.ref('estate.khl_5').id,
                    'attendance_code_id': self.att_code_k.id,
                    'activity_id': self.env.ref('estate.activity_54110_3').id,
                    'quantity': 10,
                    'location_id': self.env.ref('estate.block_1').id
                }),
                (0, 0, {
                    'employee_id': self.env.ref('estate.khl_4').id,
                    'attendance_code_id': self.att_code_k.id,
                    'activity_id': self.env.ref('estate.activity_54110_5').id,
                    'quantity': 15,
                    'location_id': self.env.ref('estate.block_2').id
                })
            ]
        }
        upkeep_second_id = self.Upkeep.sudo(self.estate_user).create(vals)
        self.assertTrue(upkeep_second_id, 'Estate user could not create another upkeep.')
        self.assertEqual(self.Labour.get_quantity(start, end, analytic, account, company)['quantity'], 30,
                         'Account productivity did not return 30')

