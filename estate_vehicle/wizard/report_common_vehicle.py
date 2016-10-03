from openerp import models, fields, api
from datetime import datetime, timedelta
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _
from openerp import tools
from openerp.exceptions import Warning


class ReportCommonVehicle(models.TransientModel):
    _name = 'report.common.vehicle'
    _description = 'Report Common Vehicle'

    period = fields.Selection([('today', 'Today'),
                               ('week', 'Weekly'),
                               ('month', 'Monthly'),
                               ('custom', 'Select Dates')], 'Period',
                              help='Select period of activities to be displayed at report.',
                              default='week') # remove for production
    date_start = fields.Date("Start Date", default=fields.Date.context_today)
    date_end = fields.Date("End Date")
    vehicle_id = fields.Many2one('fleet.vehicle','Vehicle',domain=[('maintenance_state_id','!=',False)])
    employee_id = fields.Many2one('hr.employee','Employee',)
    maintenance_state_id = fields.Many2one('asset.state','Status',domain=[('team','=','3')])
    company_id = fields.Many2one('res.company','Company')

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
    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        for record in self:
            if record.vehicle_id:
                record.company_id = record.env['res.company'].get_company(record.division_id.id)

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
        result['type'] = data['form']['type'] or False
        result['vehicle_id'] = data['form']['vehicle_id'] or False
        result['company_id'] = data['form']['company_id'] or False
        result['maintenance_state_id'] = data['form']['maintenance_state_id'] or False
        result['employee_id'] = data['form']['employee_id'] or False
        return result

    def _print_report(self, data):
        raise (_('Error!'), _('Not implemented.'))

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['period', 'date_start', 'date_end','employee_id','maintenance_state_id', 'vehicle_id', 'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        return self._print_report(data)