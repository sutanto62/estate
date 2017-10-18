# -*- coding: utf-8 -*-
from openerp import api
from openerp.tests import TransactionCase
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError

class TestRainfall(TransactionCase):

    def setUp(self):
        super(TestRainfall, self).setUp()

        self.today = datetime.today()
        self.Rainfall = self.env['estate_rainfall.rainfall']
        # self.Config = self.env['estate.config.settings'].search([],
        #                                                         order='id desc',
        #                                                         limit=1)
        #
        # self.Config.default_time_start = 17.0
        # self.Config.default_time_end = 6.0
        # self.Config.default_observation_method = 'end'
        # self.Config.default_time_overnight = True
        # self.Config.execute()
        vals = {
            'date': (self.today + relativedelta(days=1)).strftime(DF),
            'time_start': 21.0,
            'time_end': 22.0,
            'volume': 10,
            'observation': 'morning',
            'day': 1
        }

        self.rainfall = self.Rainfall.create(vals)

