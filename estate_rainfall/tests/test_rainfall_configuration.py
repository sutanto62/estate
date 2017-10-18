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

        vals = {
            'default_time_start': 17.0,
            'default_time_end': 6.0,
            'default_observation_method': 'start',
            'default_time_overnight': True
        }

        self.config_id = self.env['estate.config.settings'].create(vals)
