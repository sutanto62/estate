# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools.misc import formatLang
import openerp.addons.decimal_precision as dp
import json
import pytz


class Activity(models.Model):

    _inherit = 'estate.activity'

    kanban_dashboard = fields.Text(compute='_kanban_dashboard')
    kanban_dashboard_graph = fields.Text(compute='_kanban_dashboard_graph')

    @api.one
    def _kanban_dashboard(self):
        self.kanban_dashboard = json.dumps(self.get_upkeep_labour())

    @api.one
    def _kanban_dashboard_graph(self):
        self.kanban_dashboard_graph = json.dumps(self.get_bar_graph_datas())

    @api.multi
    def get_upkeep_labour(self):
        """ Preview output and cost of labour."""
        upkeep_labour_obj = self.env['estate.upkeep.labour']

        local = pytz.timezone(self._context['tz'])
        datetime_today_utc = pytz.utc.localize(datetime.today())
        datetime_today = datetime_today_utc.astimezone(local)

        week_start = datetime_today_utc + relativedelta(days=-datetime_today_utc.weekday())
        week_end = week_start + relativedelta(weeks=1, days=-1)
        month_start = datetime_today_utc + relativedelta(day=1)

        for record in self:
            weekly_upkeep_ids = upkeep_labour_obj.search([('activity_id', '=', record.id),
                                                          ('upkeep_date', '>=', week_start),
                                                          ('upkeep_date', '<', week_end)])

            # Recordset return multiple locations
            location_ids = []
            for item in weekly_upkeep_ids:
                if item.location_id.name not in location_ids:
                    location_ids.append(item.location_id.name)

            weekly_output = sum(item.quantity for item in weekly_upkeep_ids)
            weekly_number_of_day = sum(item.number_of_day for item in weekly_upkeep_ids)
            weekly_amount = sum(item.amount for item in weekly_upkeep_ids)

            monthtodate_upkeep_ids = upkeep_labour_obj.search([('activity_id', '=', record.id),
                                                               ('upkeep_date', '>=', month_start),
                                                               ('upkeep_date', '<', datetime_today)])
            monthtodate_output = sum(item.quantity for item in monthtodate_upkeep_ids)

        return {
            'date': datetime_today.strftime('%Y-%m-%d'),
            'count': len(weekly_upkeep_ids) if weekly_upkeep_ids else 0,
            'location_ids': location_ids.sort(),
            'weekly_output': weekly_output,
            'weekly_number_of_day': weekly_number_of_day,
            'weekly_amount': '{0:,.2f}'.format(weekly_amount),
            'output_uom': record.uom_id.name,
            'monthtodate_output': monthtodate_output,
        }

    @api.multi
    def get_bar_graph_datas(self):
        data = []
        data.append({'label': _('Past'), 'value': 15.2, 'type': 'past'})
        data.append({'label': _('Sen'), 'value': 1.2, 'type': 'future'})
        data.append({'label': _('Sel'), 'value': 11.2, 'type': 'future'})
        data.append({'label': _('Rab'), 'value': 5.7, 'type': 'future'})
        data.append({'label': _('Kam'), 'value': 7, 'type': 'future'})
        data.append({'label': _('Jum'), 'value': 1.2, 'type': 'future'})
        data.append({'label': _('Sab'), 'value': 4.2, 'type': 'future'})
        data.append({'label': _('Min'), 'value': 0.0, 'type': 'future'})
        return [{'values': data}]