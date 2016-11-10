# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv, _
import datetime, pytz
from dateutil.relativedelta import relativedelta

# Need to resolve leapday/leapyear to support weekly or daily reset period
RESET_PERIOD = [('year', 'Every Year'), ('month', 'Every Month')]
RESET_PERIOD_TIMEDELTA = [('year', 12), ('month', 1)]

def _select_nextval(cr, seq_name):
    cr.execute("SELECT nextval('%s')" % seq_name)
    return cr.fetchone()

class Sequence(models.Model):
    """Custom sequence autoreset for standard implementation sequence only."""
    _inherit = 'ir.sequence'

    auto_reset = fields.Boolean('Auto Reset', default=False)
    reset_period = fields.Selection(RESET_PERIOD, 'Reset Period', required=True)
    reset_time = fields.Datetime('Next Reset Time', help="Always set time to 00:00:00/midnight.")
    reset_init_number = fields.Integer('Reset Number', required=True, default=1,
                                       help='Reset number to this sequence')

    def _next_do(self):
        if self['implementation'] == 'standard' and self['auto_reset']:

            if self.reset_time < self.env.context.get('ir_sequence_date'):
                delta = [item for item in RESET_PERIOD_TIMEDELTA if item[0] == self.reset_period]
                reset_time_datetime = datetime.datetime.strptime(self.reset_time, '%Y-%m-%d %H:%M:%S')

                # support year/month only.
                next_reset_time = reset_time_datetime + relativedelta(months=delta[0][1])
                self.reset_time = next_reset_time
                self.number_next = self.reset_init_number

                return super(Sequence, self)._next_do()

        return super(Sequence, self)._next_do()

    def get_prefix_char(self, prefix, upkeep_date):
        """ Returns the prefix char. Follow ir_sequence.py interpolate method"""
        now = range_date = effective_date = upkeep_date
        sequences = {
            'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
            'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
        }
        res = {}
        for key, sequence in sequences.iteritems():
            res[key] = effective_date.strftime(sequence)
            res['range_' + key] = range_date.strftime(sequence)
            res['current_' + key] = now.strftime(sequence)

        if prefix:
            return prefix % res
        return ''
