# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError

class TestPayslipRun(TransactionCase):

    def setUp(self):
        super(TestPayslipRun, self).setUp()

        vals = {
            'name': 'reference',
            'date_start': '2017-01-01',
            'date_end': '2017-01-31',
            'estate_id': self.env.ref('estate_lyd'),
            'company_id': self.env.ref('base.main_company')
        }
        self.payslip_run_id = self.env['hr.payslip.run'].create(vals)

    def test_00_create_allocation(self):
        return True

    def test_01_create_receivable(self):
        return True

    def test_02_period_date(self):
        payslip_run_obj = self.env['hr.payslip.run']
        print 'testing'
        print payslip_run_obj.period_date('reference')
        self.assertEqual(1,2)

