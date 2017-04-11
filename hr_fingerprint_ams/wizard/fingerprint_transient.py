# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _
from openerp import tools
from openerp.exceptions import Warning

class UpkeepFingerprintReport(models.TransientModel):
    _name = 'hr_fingerprint_ams.fingerprint.print'
    _description = 'Upkeep Fingerprint Wizard'

    period = fields.Selection([('today', 'Today'),
                               ('week', 'Weekly'),
                               ('month', 'Monthly'),
                               ('custom', 'Select Dates')], 'Period',
                              help='Select period of activities to be displayed at report.',
                              default='week') # remove for production
    date_start = fields.Date("Start Date", default=fields.Date.context_today)
    date_end = fields.Date("End Date")
    company_id = fields.Many2one('res.company', 'Company')
    estate_id = fields.Many2one('stock.location', "Estate",
                                domain=[('estate_location', '=', True), ('estate_location_level', '=', '1'),
                                ('estate_location_type', '=', 'planted')])
    assistant_id = fields.Many2one('hr.employee', 'Assistant')

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
        # if start:
        #     to = (start + relativedelta.relativedelta(months=+1, days=-1))
        #     record.date_end = to.strftime(DF)
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
    @api.onchange('type')
    def _onchange_type(self):
        """Clear division
        """
        for record in self:
            if self.type == 'estate' and self.division_id:
                self.division_id = ''

    @api.multi
    @api.onchange('division_id')
    def _onchange_division_id(self):
        for record in self:
            if self.division_id:
                self.estate_id = self.env['stock.location'].get_estate(self.division_id.id)

    @api.multi
    @api.constrains('date_end')
    def _check_date_end(self):
        for record in self:
            if record.date_end < record.date_start:
                raise Warning(_('End Date cannot be set before Start Date.'))

    def _build_contexts(self, data):
        result = {}
        result['date_from'] = data['form']['date_start'] or False
        result['date_to'] = data['form']['date_end'] or False
        result['company_id'] = data['form']['company_id'] or False
        result['estate_id'] = data['form']['estate_id'] or False
        result['assistant_id'] = data['form']['assistant_id'] or False
        return result

    def _print_report(self, data):
        report_obj = self.env['report']
        return report_obj.with_context(landscape=True).get_action(self, 'hr_fingerprint_ams.report_upkeep_fingerprint',
                                                                  data=data)

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['period', 'date_start', 'date_end', 'company_id', 'estate_id', 'assistant_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        return self._print_report(data)

