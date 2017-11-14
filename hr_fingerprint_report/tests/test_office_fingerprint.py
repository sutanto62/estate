# -*- coding: utf-8 -*-
from openerp import api
from openerp.tests import TransactionCase
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError

class TestFingerprint(TransactionCase):

    def setUp(self):
        super(TestFingerprint, self).setUp()

    def test_00_import_office_csv(self):
        """ Import csv"""
        self.assertEqual(1,2)
