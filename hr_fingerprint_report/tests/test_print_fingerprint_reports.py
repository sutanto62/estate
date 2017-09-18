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

        # self.report_obj = self.env['report.fingerprint']
        self.data = {
            'form': {
                'date_end': '2017-08-27',
                'date_start': '2017-08-21',
                'company_id': (1, 'Heksa Jaya Abadi'),
                'office_level_id': (2, 'Estate'),
                'period': 'week',
                'contract_period': '1',
                'contract_type': '1',
                'location_id': (105, 'Estate')
            }
        }

    def test_00_get_action_reason(self):
        """ Check return action reason if any"""
        # return any
        # self.assertTrue(self.report_obj.get_attendance_remark())
        return True

