# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _

class EstateDivisionReport(models.TransientModel):
    _name = "estate.division.report"
    _inherit = "estate.common.report"
    _description = "Division Report"

    def _print_report(self, data):
        return self.env['report'].with_context(landscape=True).get_action(self, 'estate.report_estate_division', data=data)