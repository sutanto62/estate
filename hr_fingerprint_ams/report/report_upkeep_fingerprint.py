#-*- coding:utf-8 -*-

from openerp import api, models


class UpkeepFingerprintReport(models.AbstractModel):
    _name = 'report.hr_fingerprint_ams.report_upkeep_fingerprint'

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

        fingerprint_ids = obj.search(domain)
        return fingerprint_ids

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('hr_fingerprint_ams.report_upkeep_fingerprint')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'report': data,
            'Fingerprint': self._get_fingerprint(data),
        }
        return report_obj.render('hr_fingerprint_ams.report_upkeep_fingerprint', docargs)