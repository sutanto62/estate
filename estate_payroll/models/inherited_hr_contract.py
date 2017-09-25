# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
from openerp.tools.translate import _
from openerp.exceptions import ValidationError, UserError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from datetime import datetime
from dateutil import relativedelta

class Contract(models.Model):
    """ Contract date not match with upkeep labour"""
    _inherit = 'hr.contract'

    @api.model
    def _default_date_start(self):
        """ Make sure contract date start is first date of the month."""
        return datetime.today() + relativedelta.relativedelta(day=1)

    date_start = fields.Date(default=_default_date_start)

    @api.multi
    @api.constrains('date_start')
    def _check_date_start(self):
        """ Make sure contract and upkeep synced."""
        for record in self:
            # contract is yearly base
            earliest_date = datetime.today() + relativedelta.relativedelta(month=1,day=1)
            latest_date = datetime.today() + relativedelta.relativedelta(month=12,day=31)

            # upkeep labor only
            upkeep_ids = self.env['estate.upkeep.labour'].search([('upkeep_date', '>=', earliest_date),
                                                                  ('upkeep_date', '<=', latest_date),
                                                                  ('employee_id', '=', record.employee_id.id)],
                                                                 order='upkeep_date asc')
            if upkeep_ids:
                if record.date_start > upkeep_ids[0].upkeep_date:
                    err_msg = _('We found there was upkeep at %s.\n'
                                'Please set your employee contract date at first date of the month.'
                                % upkeep_ids[0].upkeep_date)
                    raise ValidationError(err_msg)
            else:
                return True