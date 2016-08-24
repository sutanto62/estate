# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase


class TestPayslipRun(TransactionCase):

    def setUp(self):
        super(TestPayslipRun, self).setUp()
        self.payslip_run = self.env.ref('estate_payroll.estate_payroll_1')

    def test_00_create(self):
        """ Check state """
        self.assertTrue(self.payslip_run)
        self.assertEqual(self.payslip_run.state, 'draft', 'Estate Payroll: payslip batches created not in draft')
        for payslip in self.payslip_run.slip_ids:
            self.assertEqual(payslip.state, 'draft', 'Estate Payroll: payslip created not in draft')

    def test_00_close_payslip_run(self):
        # Imitate when human resources manager close payslip batch
        self.payslip_run.close_payslip_run()
        self.assertEqual(self.payslip_run.state, 'close', 'Estate Payslip: close_payslip_run did not close payslip run')
        for payslip in self.payslip_run.slip_ids:
            self.assertEqual(payslip.state, 'close', 'Estate Payslip: close_payslip_run did not close payslip')

    def test_00_draft_payslip_run(self):
        self.payslip_run.draft_payslip_run()
        self.assertEqual(self.payslip_run.state, 'draft',
                         'Estate Payslip: draft_payslip_run did not draft payslip run')
        for payslip in self.payslip_run.slip_ids:
            self.assertEqual(payslip.state, 'draft', 'Estate Payslip: draft_payslip_run did not draft payslip')

    def test_00_unlink(self):
        pass

# def test_create_payslip_run(self):
#     """ Create payslip run """
#
#     self.assertTrue(self.payslip_run, 'Payslip Run: no payslip run created.')
#
#     # Payslip Run and its line should be in draft state
#     self.assertEqual(self.payslip_run.state, 'draft', 'Payslip Run: payslip batches created not in draft')
#     for payslip in self.payslip_run.slip_ids:
#         self.assertEqual(payslip.state, 'draft', '-- Payslip: payslip created not in draft')
#
# def test_draft_payslip_run(self):
#     """ Open payslip run """
#
#     # Imitate when human resources manager close payslip batch
#     self.payslip_run.draft_payslip_run()
#     self.assertEqual(self.payslip_run.state, 'draft', 'Payslip Run: payslip batches not in open')
#     for payslip in self.payslip_run.slip_ids:
#         self.assertEqual(payslip.state, 'draft', '-- Payslip: payslip state not draft')
#     for upkeep in self.Upkeep.search([('date', '>=', self.date_1), ('date', '<=', self.date_2)]):
#         self.assertEqual(upkeep.state, 'approved', '-- Upkeep: upkeep state not payslip')
#         for activity in upkeep:
#             self.assertEqual(activity.state, 'approved', '---- Activity: activity state not in approved')
#         for labour in upkeep:
#             self.assertEqual(labour.state, 'approved', '---- Labour: labour state not in approved')
#         for material in upkeep:
#             self.assertEqual(material.state, 'approved', '---- Material: material state not in approved')
#
# def test_close_payslip_run(self):
#     """ Close payslip run """
#
#     # Imitate when human resources manager close payslip batch
#     self.payslip_run.close_payslip_run()
#     self.assertEqual(self.payslip_run.state, 'close', 'Payslip Run: payslip run state is not close')

# for payslip in self.payslip_run.slip_ids:
#     self.assertEqual(payslip.state, 'done', '-- Payslip: payslip state not done')
#
# for upkeep in self.Upkeep.search([('date', '>=', self.date_1), ('date', '<=', self.date_2)]):
#     self.assertEqual(upkeep.state, 'payslip', '-- Upkeep: upkeep state not payslip')
#     for activity in upkeep:
#         self.assertEqual(activity.state, 'payslip', '---- Activity: activity state not in payslip')
#     for labour in upkeep:
#         self.assertEqual(labour.state, 'payslip', '---- Labour: labour state not in payslip')
#     for material in upkeep:
#         self.assertEqual(material.state, 'payslip', '---- Material: material state not in payslip')
#         datetime.strptime()

# def test_report_estate_payslip(self):
#
#     for payslip in self.payslip_run.slip_ids:
#         rep = self.Report(payslip)
#         print rep