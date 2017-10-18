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

        # setup
        vals = {
            'default_time_start': 17.0,
            'default_time_end': 6.0,
            'default_observation_method': 'start',
            'default_time_overnight': True
        }
        self.config_id = self.env['estate.config.settings'].create(vals)

        # a rainfall
        self.today = datetime.today()
        self.Rainfall = self.env['estate_rainfall.rainfall']
        vals = {
            'date': (self.today + relativedelta(days=1)).strftime(DF),
            'time_start': 21.0,
            'time_end': 22.0,
            'volume': 10,
            'observation': 'morning',
            'day': 0,
            'duration': 1.0
        }
        self.rainfall = self.Rainfall.create(vals)

    def test_00_onchange_time_evening(self):
        """ I checked observation period based on rainfall configuration."""
        self.rainfall.time_start = 10.0
        self.rainfall._onchange_time()
        self.assertEqual(self.rainfall.observation, 'evening')

    def test_01_onchange_time_morning(self):
        """ I checked if time_start update changed observation."""
        self.rainfall.time_start = 19.0
        self.rainfall._onchange_time()
        self.assertEqual(self.rainfall.observation, 'morning')

    def test_02_onchange_volume(self):
        """ I checked rainfall day."""

        # volume and condition not zero
        self.rainfall._onchange_volume()
        self.assertEqual(self.rainfall.day, 1)

    def test_03_onchange_volume_zero(self):
        """ I checked zero volume."""
        with self.assertRaises(ValidationError):
            self.rainfall.volume = 0

    def test_04_compute_duration(self):
        """ I checked duration computation."""

        # update time_start and time_end to zero
        vals = {
            'time_start': 0.0,
            'time_end': 0.0
        }
        self.rainfall.write(vals)
        self.assertEqual(self.rainfall.duration, 0.0)

        # update to non zero
        vals = {
            'time_start': 21.0,
            'time_end': 21.5
        }
        self.rainfall.write(vals)
        self.assertEqual(self.rainfall.duration, 0.5)

    def test_05_check_time(self):
        """ I checked maxiumm time start or end"""

        # time_start
        with self.assertRaises(ValidationError):
            self.rainfall.write({'time_start': 24.1})

        # time_end
        with self.assertRaises(ValidationError):
            self.rainfall.write({'time_end': 24.1})
