# -*- coding: utf-8 -*-

import logging
from openerp import models, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

_logger = logging.getLogger(__name__)


class InheritUpkeepLabour(models.Model):

    _inherit = 'estate.upkeep.labour'

    @api.constrains('attendance_code_id')
    def _check_attendance_code(self):
        """ Piece rate attendance code used only if monthly number of days > 20."""
        monthly_limit = 20.0

        att_code = self.env['estate.hr.attendance'].search([('piece_rate', '=', False)]).ids
        start = datetime.strptime(self.upkeep_date, DF).replace(day=1)
        if start:
            end = (start + relativedelta(months=+1, days=-1))

#         upkeep_ids = self.env['estate.upkeep.labour'].search([('employee_id', '=', self.employee_id.id),
#                                                               ('upkeep_date', '>=', start),
#                                                               ('upkeep_date', '<=', end),
#                                                               ('attendance_code_id', 'in', att_code)])
# 
#         regular_number_of_days = sum(item.number_of_day for item in upkeep_ids) + (self.number_of_day if not self.attendance_code_id.piece_rate else 0) 
#         
#         if not self.attendance_code_id.piece_rate and (regular_number_of_days > monthly_limit):
#             # check if month to date exceed monthly limit.
#             err_msg = _('%s will exceed  %s number of days. Use piece rate attendance code.' % (self.employee_id.name, monthly_limit))
#             raise ValidationError(err_msg)
#         elif self.attendance_code_id.piece_rate and (regular_number_of_days < monthly_limit):
#             # prevent piece rate attendance code used before total exceed monthly limit
#             err_msg = _('%s has not exceed %s number of days yet. Use regular attendance' % (self.employee_id.name, monthly_limit))
#             raise ValidationError(err_msg)

        upkeep_ids = self.env['estate.upkeep.labour'].search([('employee_id', '=', self.employee_id.id),
                                                          ('upkeep_date', '>=', start),
                                                          ('upkeep_date', '<=', end)])

        regular_number_of_days_hk = sum(item.number_of_day for item in upkeep_ids if item.attendance_code_id.piece_rate != True)
        regular_number_of_days_pr = sum(item.number_of_day for item in upkeep_ids if item.attendance_code_id.piece_rate == True) 
        
        new_record = True if sum(item.number_of_day for item in upkeep_ids if item.id == self.id) == 0 else False
        
#         err_msg = _('HK %s  PR %s Existing %s' % (regular_number_of_days_hk, regular_number_of_days_pr, new_record))
        
        if new_record:
            if self.attendance_code_id.piece_rate != True:
                if regular_number_of_days_hk + self.number_of_day >  monthly_limit: 
                    err_msg = _('%s will exceed  %s number of days. Use piece rate attendance code.' % (self.employee_id.name, monthly_limit))
                    raise ValidationError(err_msg)
            else:
                if regular_number_of_days_hk < monthly_limit: 
                    err_msg = _('%s has not exceed %s number of days yet. Use regular attendance' % (self.employee_id.name, monthly_limit))
                    raise ValidationError(err_msg)        
        else:
            if regular_number_of_days_hk > monthly_limit:
                err_msg = _('%s will exceed  %s number of days. Use piece rate attendance code.' % (self.employee_id.name, monthly_limit))
                raise ValidationError(err_msg)
            if regular_number_of_days_hk <= monthly_limit and regular_number_of_days_pr > 0: 
                    err_msg = _('%s has not exceed %s number of days yet. Use regular attendance' % (self.employee_id.name, monthly_limit))
                    raise ValidationError(err_msg)
        
        return super(InheritUpkeepLabour, self)._check_attendance_code()
