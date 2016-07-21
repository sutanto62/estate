# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from openerp.addons.hr_payroll import hr_payroll
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from estate_payroll.report import report_estate_payslip as RF

class TestPayslipRun(TransactionCase):

    def setUp(self):
        super(TestPayslipRun, self).setUp()
        # Models
        self.PayslipRun = self.env['hr.payslip.run']
        self.Upkeep = self.env['estate.upkeep']
        # self.Report = RF.estate_payslip_run_report
        self.Contract = self.env['hr.contract']
        self.date_1 = (datetime.today() + relativedelta.relativedelta(day=1)).strftime(DF)
        self.date_2 = ((datetime.today() + relativedelta.relativedelta(day=1)) + relativedelta.relativedelta(months=+1, days=-1)).strftime(DF)
        # Record
        self.estate = self.env.ref('stock.stock_main_estate')
        self.khl_1 = self.env.ref('hr_employee.khl_1')
        self.kht_1 = self.env.ref('hr_employee.khl_3')
        self.khl_9 = self.env.ref('hr_employee.khl_9')  # has no team

        # Set upkeep demo state to approved
        upkeep_ids = self.Upkeep.search([('date', '>=', self.date_1),
                                         ('date', '<=', self.date_2)])
        upkeep_ids.write({'state': 'approved'})

        # Uncomment to display upkeep detail
        # for upkeep in upkeep_ids:
        #     print 'upkeep ... %s (state: %s)' % (upkeep.name, upkeep.state)
        #     for activity in upkeep.activity_line_ids:
        #         print '-- activity ... %s (state: %s)' % (activity.name, activity.state)
        #     for labour in upkeep.labour_line_ids:
        #         print '-- labour ...%s (state: %s)' % (labour.employee_id.name, labour.state)
        #     for material in upkeep.material_line_ids:
        #         print '-- material ... %s (state: %s)' % (material.product_id.name, material.state)

        # Create payslip batch
        payslip_vals = {
            'name': 'Payslip Run',
            'date_start': self.date_1,
            'date_end': self.date_2,
            'type': 'estate',
            'estate_id': self.estate.id,
            'slip_ids': [
                (0, 0, {
                    'employee_id': self.khl_1.id,
                    'date_from': self.date_1,
                    'date_to': self.date_2,
                }),
                (0, 0, {
                    'employee_id': self.khl_9.id,
                    'date_from': self.date_1,
                    'date_to': self.date_2,
                }),
                (0, 0, {
                    'employee_id': self.kht_1.id,
                    'date_from': self.date_1,
                    'date_to': self.date_2,
                })
            ]
        }

        # Imitate what happens in the controller when somebody creates a new payslip batch
        self.payslip_run = self.PayslipRun.create(payslip_vals)

    def test_get_team(self):
        """ Check _get_team """

        for payslip in self.payslip_run.slip_ids:
            payslip._get_team()
            if payslip.employee_id == self.env.ref('hr_employee.khl_9'):
                self.assertFalse(payslip.team_id, '-- Payslip: _get_team should not return team')
            else:
                self.assertTrue(payslip.team_id, '-- Payslip: _get_team did not return team')

    def test_get_worked_day_lines(self):
        """ Check get_worked_day_lines, input_lines and compute_sheet """

        for payslip in self.payslip_run.slip_ids:
            # payslip compute worked days
            hr_payroll.hr_payslip.onchange_employee(payslip)
            # Checked worked day lines
            self.assertEqual(payslip.worked_days_line_ids['code'], 'WORK300', '-- Payslip: _get_worked_day_lines do not return number of days')
            # Checked input lines
            for input in payslip.input_line_ids:
                self.assertIn(input['code'], ['PR', 'OT'], '-- Payslip: _get_inputs do not return PR or OT')
            # Checked salary detail
            hr_payroll.hr_payslip.compute_sheet(payslip)
            for line in payslip.line_ids:
                self.assertIn(line['code'], ['EDW', 'PR', 'OT', 'BPJSPKWTC',
                                             'BPJSPKWTE', 'JHTC', 'JHTE', 'JKKC',
                                             'JKMC'], '-- Payslip: _get_inputs do not return payslip line')

    def test_create_payslip_run(self):
        """ Create payslip run """

        self.assertTrue(self.payslip_run, 'Payslip Run: no payslip run created.')

        # Payslip Run and its line should be in draft state
        self.assertEqual(self.payslip_run.state, 'draft', 'Payslip Run: payslip batches created not in draft')
        for payslip in self.payslip_run.slip_ids:
            self.assertEqual(payslip.state, 'draft', '-- Payslip: payslip created not in draft')

    def test_draft_payslip_run(self):
        """ Open payslip run """

        # Imitate when human resources manager close payslip batch
        self.payslip_run.draft_payslip_run()
        self.assertEqual(self.payslip_run.state, 'draft', 'Payslip Run: payslip batches not in open')
        for payslip in self.payslip_run.slip_ids:
            self.assertEqual(payslip.state, 'draft', '-- Payslip: payslip state not draft')
        for upkeep in self.Upkeep.search([('date', '>=', self.date_1), ('date', '<=', self.date_2)]):
            self.assertEqual(upkeep.state, 'approved', '-- Upkeep: upkeep state not payslip')
            for activity in upkeep:
                self.assertEqual(activity.state, 'approved', '---- Activity: activity state not in approved')
            for labour in upkeep:
                self.assertEqual(labour.state, 'approved', '---- Labour: labour state not in approved')
            for material in upkeep:
                self.assertEqual(material.state, 'approved', '---- Material: material state not in approved')

    def test_close_payslip_run(self):
        """ Close payslip run """

        # Imitate when human resources manager close payslip batch
        self.payslip_run.close_payslip_run()
        self.assertEqual(self.payslip_run.state, 'close', 'Payslip Run: payslip batches not in close')
        for payslip in self.payslip_run.slip_ids:
            self.assertEqual(payslip.state, 'done', '-- Payslip: payslip state not done')
        for upkeep in self.Upkeep.search([('date', '>=', self.date_1), ('date', '<=', self.date_2)]):
            self.assertEqual(upkeep.state, 'payslip', '-- Upkeep: upkeep state not payslip')
            for activity in upkeep:
                self.assertEqual(activity.state, 'payslip', '---- Activity: activity state not in payslip')
            for labour in upkeep:
                self.assertEqual(labour.state, 'payslip', '---- Labour: labour state not in payslip')
            for material in upkeep:
                self.assertEqual(material.state, 'payslip', '---- Material: material state not in payslip')

    # def test_report_estate_payslip(self):
    #
    #     for payslip in self.payslip_run.slip_ids:
    #         rep = self.Report(payslip)
    #         print rep

