# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError
from datetime import date, datetime, time
from dateutil import relativedelta
from decimal import *

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT


class TestFingerprintReport(TransactionCase):

    def setUp(self):
        super(TestFingerprintReport, self).setUp()
        self.Report = self.env['report.hr_fingerprint_report.report_fingerprint']
        self.department_id = self.env['hr.department'].create({'name':'Department'})
        self.data = {
            'form': {
                'date_end': '2017-08-27',
                'date_start': '2017-08-21',
                'company_id': (1, 'Heksa Jaya Abadi'),
                'office_level_id': (2, 'Estate'),
                'department_id': (self.department_id.id, self.department_id.name),
                'period': 'week',
                'contract_period': '1',
                'contract_type': '1',
                'location_id': (105, 'Estate')
            }
        }

    def test_00_get_domain(self):
        self.Report.get_domain(self.data)
