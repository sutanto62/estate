# -*- coding: utf-8 -*-

from openerp import api
from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp import tools
from dateutil.relativedelta import relativedelta
import json
import pytz


class TestEstateDashboard(TransactionCase):

    def setUp(self):
        super(TestEstateDashboard, self).setUp()

        self.Activity = self.env['estate.activity']
    #
    # def test_00_get_upkeep_labour(self):
    #
    #     local = pytz.timezone('Asia/Jakarta')
    #
    #     datetime_today_utc = pytz.utc.localize(datetime.today())
    #     datetime_today = datetime_today_utc.astimezone(local)
    #
    #
    #     week_start = datetime_today_utc + relativedelta(days=-datetime_today_utc.weekday())
    #     week_end = week_start + relativedelta(weeks=1, days=-1)
    #
    #     month_start = datetime_today_utc + relativedelta(day=1)

