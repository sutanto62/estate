# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv, _
import pytz
import time

from datetime import datetime, timedelta
from openerp.exceptions import UserError

# class Sequence(models.Model):
#     """Default sequence did not contain contract type, company or estate."""
#
#     _inherit = 'ir.sequence'
#
#     def get_next_char(self, number_next):
#         """type, company and estate prefix not supported at sequence"""
#
#         def _interpolate(s, d):
#             """Unable to inherit sub method of method"""
#             if s:
#                 return s % d
#             return ''
#
#         def _interpolation_dict():
#             """Unable to inherit sub method of method"""
#             now = range_date = effective_date = datetime.now(pytz.timezone(self.env.context.get('tz') or 'UTC'))
#             if self.env.context.get('ir_sequence_date'):
#                 effective_date = datetime.strptime(self.env.context.get('ir_sequence_date'), '%Y-%m-%d')
#             if self.env.context.get('ir_sequence_date_range'):
#                 range_date = datetime.strptime(self.env.context.get('ir_sequence_date_range'), '%Y-%m-%d')
#
#             # Add context checker here
#             contract_type = estate = ''
#             if self.env.context.get('ir_sequence_contract_type'):
#                 contract_type = self.env.context.get('ir_sequence_contract_type')
#             if self.env.context.get('ir_sequence_estate'):
#                 estate = self.env.context.get('ir_sequence_estate')
#
#             # Add new prefix here ...
#             sequences = {
#                 'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
#                 'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S', 'type': contract_type, 'estate': estate
#             }
#             res = {}
#             for key, sequence in sequences.iteritems():
#                 res[key] = effective_date.strftime(sequence)
#                 res['range_' + key] = range_date.strftime(sequence)
#                 res['current_' + key] = now.strftime(sequence)
#             return res
#
#         # Add condition to catch new prefix here.
#         if 'type' in self.prefix:
#             # Use type as common of nik prefix
#             d = _interpolation_dict()
#
#             try:
#                 interpolated_prefix = _interpolate(self.prefix, d)
#                 interpolated_suffix = _interpolate(self.suffix, d)
#             except ValueError:
#                 raise UserError(_('Invalid prefix or suffix for sequence \'%s\'') % (self.get('name')))
#
#             res = interpolated_prefix + '%%0%sd' % self.padding % number_next + interpolated_suffix
#             return res
#         else:
#             return super(Sequence, self).get_next_char(number_next)
