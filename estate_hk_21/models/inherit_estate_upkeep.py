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
        """ Override estate upkeep."""
        monthly_limit = 20
        monthly_worked_days = 0

        att_code = self.env['estate.hr.attendance'].search([('piece_rate', '=', False)]).ids
        start = datetime.strptime(self.upkeep_date, DF).replace(day=1)
        if start:
            end = (start + relativedelta(months=+1, days=-1))

        print '_check_attendance_code start:%s, end:%s' % (start,end)

        upkeep_ids = self.env['estate.upkeep.labour'].search([('employee_id', '=', self.employee_id.id),
                                                              ('upkeep_date', '>=', start),
                                                              ('upkeep_date', '<=', end),
                                                              ('attendance_code_id', 'in', att_code)])

        # Validate only attendance code withouth piece rate day
        if self.attendance_code_id.piece_rate is False:
            monthly_worked_days = sum(item.number_of_day for item in upkeep_ids) + self.number_of_day

        print '_check_attendance_code %s' % monthly_worked_days

        if monthly_worked_days > monthly_limit:
            error_msg = _("%s has been work for more than %s days." % (self.employee_id.name, monthly_limit))
            raise ValidationError(error_msg)

        return super(InheritUpkeepLabour, self)._check_attendance_code()
