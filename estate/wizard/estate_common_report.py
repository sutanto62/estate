# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _

class EstateCommonReport(models.TransientModel):
    _name = 'estate.common.report'
    _description = 'Estate Common Report'

    period = fields.Selection([('today', 'Today'),
                               ('week', 'This Week'),
                               ('month', 'This Month'),
                               ('custom', 'Select dates')], 'Period',
                              help='Select period of activities to be displayed at report.',
                              default='week') # remove for production
    # date_start = fields.Date("Start Date", default=fields.Date.context_today)
    # date_end = fields.Date("End Date", default=fields.Date.context_today)
    date_start = fields.Date("Start Date", default='2016-05-01')  # remove for production
    date_end = fields.Date("End Date", default='2016-05-31')  # remove for production
    type = fields.Selection([('estate', 'By Estate'),
                             ('division', 'By Division')],
                            'Group By', help='*By Estate, shows all activities.'
                                                '*By Division, group activities by Division.',
                            default='division')
    estate_id = fields.Many2one('stock.location', "Estate",
                                domain=[('estate_location', '=', True), ('estate_location_level', '=', '1'),
                                ('estate_location_type', '=', 'planted')],
                                default='stock.stock_main_estate')  # todo remove for production
    division_id = fields.Many2one('stock.location', "Division",
                                  domain=[('estate_location', '=', True), ('estate_location_level', '=', '2')],
                                  default ='stock.stock_division_1')  # todo remove for production

    @api.multi
    @api.onchange('date_start')
    def _onchange_date_start(self):
        """Set default report in a month period
        """
        for record in self:
            start = datetime.strptime(record.date_start, DF).replace(day=1)
            if start:
                to = (start + relativedelta.relativedelta(months=+1, days=-1))
                record.date_end = to.strftime(DF)

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



    def _build_contexts(self, data):
        result = {}
        result['date_from'] = data['form']['date_start'] or False
        result['date_to'] = data['form']['date_end'] or False
        result['type'] = data['form']['type'] or False
        result['estate_id'] = data['form']['estate_id'] or False
        result['division_id'] = data['form']['division_id'] or False
        return result

    def _print_report(self, data):
        raise (_('Error!'), _('Not implemented.'))

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['period', 'date_start', 'date_end', 'type', 'estate_id', 'division_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        return self._print_report(data)