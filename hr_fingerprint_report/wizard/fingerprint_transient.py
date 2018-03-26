# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _
from openerp import tools
from openerp.exceptions import Warning

class Fingerprint(models.TransientModel):
    _name = 'hr_fingerprint_report.fingerprint.wizard'
    _description = 'Fingerprint Wizard'

    period = fields.Selection([('today', 'Today'),
                               ('week', 'Weekly'),
                               ('month', 'Monthly'),
                               ('custom', 'Select Dates')], 'Period',
                              help='Select period of activities to be displayed at report.',
                              default='week')
    date_start = fields.Date("Start Date", default=fields.Date.context_today)
    date_end = fields.Date("End Date")
    company_id = fields.Many2one('res.company', 'Company')
    department_id = fields.Many2one('hr.department', 'Department',
                                    help='Select employee department. It may differ from AMS Department')
    contract_type = fields.Selection([('1', 'PKWTT'), ('2', 'PKWT')], "Contract Type",
                                     help="* PKWTT, Perjanjian Kerja Waktu Tidak Tertentu, " \
                                          "* PKWT, Perjanjian Kerja Waktu Tertentu.")
    contract_period = fields.Selection([('1', 'Monthly'), ('2', 'Daily')], "Contract Period",
                                       help="* Monthly, Karyawan Bulanan, " \
                                            "* Daily, Karyawan Harian.")
    contract = fields.Boolean('Contract Based', help='Select to filter contract based.')
    location_id = fields.Many2one('hr_indonesia.location', 'Placement Location')
    office_level_id = fields.Many2one('hr_indonesia.office', 'Office Level')

    @api.multi
    @api.onchange('period')
    def _onchange_period(self):
        """User doesn't have to set date and end.
        """
        today = fields.Date.context_today(self)
        datetime_today = datetime.strptime(today, tools.DEFAULT_SERVER_DATE_FORMAT)
        for record in self:
            period = record.period
            if period == 'today':
                start = datetime_today
                record.date_start = start
                record.date_end = start
            elif period == 'week':
                start = datetime_today - timedelta(days=datetime_today.weekday())
                record.date_start = start
                record.date_end = start + timedelta(days=6)
            elif period == 'month':
                start = datetime_today.replace(day=1)
                end = start + relativedelta.relativedelta(months=+1, days=-1)
                record.date_start = start
                record.date_end = end
            else:
                record.date_start = ''
                record.date_end = ''

    @api.multi
    @api.onchange('date_start')
    def _onchange_date_start(self):
        for record in self:
            period = record.period

            # Custom period set date start empty
            if record.date_start:
                datetime_start = datetime.strptime(record.date_start, DF)

            if period == 'today':
                record.date_start = datetime_start
                record.date_end = datetime_start
            elif period == 'week':
                start = datetime_start - timedelta(days=datetime_start.weekday())
                record.date_start = start
                record.date_end = start + timedelta(days=6)
            elif period == 'month':
                start = datetime_start.replace(day=1)
                end = start + relativedelta.relativedelta(months=+1, days=-1)
                record.date_start = start
                record.date_end = end

    @api.multi
    @api.constrains('date_end')
    def _check_date_end(self):
        for record in self:
            if record.date_end < record.date_start:
                raise Warning(_('End Date cannot be set before Start Date.'))

    def _build_contexts(self, data):
        result = {}
        result['date_start'] = data['form']['date_start'] or False
        result['date_end'] = data['form']['date_end'] or False
        result['company_id'] = data['form']['company_id'] or False
        result['department_id'] = data['form']['department_id'] or False
        result['contract_type'] = data['form']['contract_type'] or False
        result['contract_period'] = data['form']['contract_period'] or False
        result['contract'] = data['form']['contract'] or False
        result['office_level_id'] = data['form']['office_level_id'] or False

        return result

    def _print_report(self, data):
        # call report action
        return self.env['report'].get_action(self, 'hr_fingerprint_report.report_fingerprint', data=data)

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['period', 'date_start', 'date_end', 'company_id', 'department_id', 'contract_id',
                                  'contract_type', 'contract_period','contract','office_level_id'])[0]

        return self._print_report(data)