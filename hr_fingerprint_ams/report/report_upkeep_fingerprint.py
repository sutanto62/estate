# -*- coding: utf-8 -*-

from openerp import api, models
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from babel.dates import format_datetime, format_date, format_time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

import pytz


class UpkeepFingerprintReport(models.AbstractModel):
    _name = 'report.hr_fingerprint_ams.report_upkeep_fingerprint'

    @api.multi
    def format_date(self, att_date, format=None):
        """
        datetime saved in UTC format.
        Args:
            att_date: string, attendance datetime
        Returns: sting, date using user locale
        """
        lang = self.env.context.get('lang', 'en_US')

        if att_date:
            utc = pytz.timezone('UTC')
            local = pytz.timezone(self._context['tz'])
            utc_date = utc.localize(datetime.strptime(att_date, format or DT))
            res = utc_date.astimezone(local)
            return format_date(res, locale=lang)

        return False

    @api.multi
    def format_time(self, att_date, format=None):
        """
        datetime saved in UTC format.
        Args:
            att_date: string, attendance datetime
        Returns: sting, time using user locale
        """
        lang = self.env.context.get('lang', 'en_US')

        if att_date:
            utc = pytz.timezone('UTC')
            local = pytz.timezone(self._context['tz'])
            utc_date = utc.localize(datetime.strptime(att_date, format or DT))
            res = utc_date.astimezone(local)
            return format_time(res, locale=lang)

        return False

    @api.multi
    def _get_fingerprint(self, data):
        """Report called by wizard has no recordset (docs)"""
        obj = self.env['hr_fingerprint_ams.fingerprint']

        domain = []

        domain.append(('state', '=', 'attendance'))

        if data['form']['date_start']:
            domain.append(('date', '>=', data['form']['date_start']))

        if data['form']['date_end']:
            domain.append(('date', '<=', data['form']['date_end']))

        if data['form']['company_id']:
            domain.append(('company_id', '=', data['form']['company_id'][0]))

        if data['form']['estate_id']:
            domain.append(('estate_id', '=', data['form']['estate_id'][0]))

        if data['form']['assistant_id']:
            domain.append(('assistant_id', '=', data['form']['assistant_id'][0]))

        fingerprint_ids = obj.search(domain)
        return fingerprint_ids

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('hr_fingerprint_ams.report_upkeep_fingerprint')

        if data and data['form']['company_id']:
            company = self.env['res.company'].browse(data['form']['company_id'][0])

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'report': data,
            'Fingerprint': self._get_fingerprint(data),
            'format_date': self.format_date,
            'format_time': self.format_time,
            'company': company,
        }
        return report_obj.render('hr_fingerprint_ams.report_upkeep_fingerprint', docargs)