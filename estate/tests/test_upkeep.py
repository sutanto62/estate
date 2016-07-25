# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from openerp.addons.hr_payroll import hr_payroll
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from estate_payroll.report import report_estate_payslip as RF

class TestUpkeep(TransactionCase):

    def setUp(self):
        super(TestUpkeep, self).setUp()
        self.Upkeep = self.env['estate.upkeep']
        self.Activity = self.env['estate.upkeep.activity']
        self.Labour = self.env['estate.upkeep.labour']
        self.Material = self.env['estate.upkeep.material']