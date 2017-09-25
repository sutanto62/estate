# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _

class AccountProductivityReport(models.TransientModel):
    _name = "estate_account.productivity.report"
    _inherit = "estate.common.report"
    _description = "Account Productivity Report"

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          domain=[('use_estate', '=', True)])
    upkeep = fields.Selection([('paid', 'Paid (Journaled)'),
                               ('payslip', 'Payslip Prepared'),
                               ('approved', 'Approved Upkeep'),
                               ('all', 'All Upkeep')], 'Upkeep',
                              help="*Paid (Journaled) - Payslip has been closed and journal entries created.\n"
                              "*Payslip Prepared - Payslip has been created.\n"
                              "*Approved Upkeep - All BKM has been approved by Estate Manager.\n"
                              "*All Upkeep - All BKM")

    def _print_report(self, data):
        return self.env['report'].with_context(landscape=True).get_action(self, 'estate.report_estate_division', data=data)
