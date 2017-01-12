# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv, _
import pytz
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp.exceptions import UserError

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
    reset_period = fields.Selection(RESET_PERIOD, 'Reset Period')
    reset_time = fields.Datetime('Next Reset Time', help="Always set time to 00:00:00/midnight.")
    reset_init_number = fields.Integer('Reset Number', default=1,
                                       help='Reset number to this sequence')

    def _next_do(self):
        if self['implementation'] == 'standard' and self['auto_reset']:

            if self.reset_time < self.env.context.get('ir_sequence_date'):
                delta = [item for item in RESET_PERIOD_TIMEDELTA if item[0] == self.reset_period]
                reset_time_datetime = datetime.strptime(self.reset_time, '%Y-%m-%d %H:%M:%S')

                # support year/month only.
                next_reset_time = reset_time_datetime + relativedelta(months=delta[0][1])
                self.reset_time = next_reset_time
                self.number_next = self.reset_init_number

                return super(Sequence, self)._next_do()

        return super(Sequence, self)._next_do()

    def get_next_char(self, number_next):
        """Add new legend for prefix or suffix.
        There are 5 custom code.
        code_1 with_context ir_sequence_code_1
        code_2 with_context ir_sequence_code_2
        code_3 with_context ir_sequence_code_3
        code_4 with_context ir_sequence_code_4
        code_5 with_context ir_sequence_code_5
        """

        def _interpolate(s, d):
            """Unable to inherit sub method of method"""
            if s:
                return s % d
            return ''

        def _interpolation_dict():
            """Unable to inherit sub method of method"""
            now = range_date = effective_date = datetime.now(pytz.timezone(self.env.context.get('tz') or 'UTC'))
            if self.env.context.get('ir_sequence_date'):
                effective_date = datetime.strptime(self.env.context.get('ir_sequence_date'), '%Y-%m-%d')
            if self.env.context.get('ir_sequence_date_range'):
                range_date = datetime.strptime(self.env.context.get('ir_sequence_date_range'), '%Y-%m-%d')

            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
            }

            # Add necessary custom code here
            code_1 = code_2 = code_3 = code_4 = code_5 = ''
            if self.env.context.get('ir_sequence_code_1'):
                code_1 = self.env.context.get('ir_sequence_code_1')
                sequences['code_1'] = code_1
            if self.env.context.get('ir_sequence_code_2'):
                code_2 = self.env.context.get('ir_sequence_code_2')
                sequences['code_2'] = code_2
            if self.env.context.get('ir_sequence_code_3'):
                code_3 = self.env.context.get('ir_sequence_code_3')
                sequences['code_3'] = code_3
            if self.env.context.get('ir_sequence_code_4'):
                code_4 = self.env.context.get('ir_sequence_code_4')
                sequences['code_4'] = code_4
            if self.env.context.get('ir_sequence_code_5'):
                code_5 = self.env.context.get('ir_sequence_code_5')
                sequences['code_5'] = code_5

            res = {}
            for key, sequence in sequences.iteritems():
                res[key] = effective_date.strftime(sequence)
                res['range_' + key] = range_date.strftime(sequence)
                res['current_' + key] = now.strftime(sequence)
            return res

        # Add condition to catch new prefix here.
        if self.prefix:
            if 'code' in self.prefix:
                # Use type as common of nik prefix
                d = _interpolation_dict()
                try:
                    interpolated_prefix = _interpolate(self.prefix, d)
                    interpolated_suffix = _interpolate(self.suffix, d)
                except ValueError:
                    raise UserError(_('Invalid prefix or suffix for sequence \'%s\'') % (self.get('name')))

                res = interpolated_prefix + '%%0%sd' % self.padding % number_next + interpolated_suffix
                return res
            else:
                return super(Sequence, self).get_next_char(number_next)

