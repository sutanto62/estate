# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
import logging
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT

_logger = logging.getLogger(__name__)


class Contract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    @api.constrains('date_start', 'date_end')
    def _check_date_start(self):
        """ Prevent overlap multiple contract date."""
        for rec in self:
            # check against latest contract
            contract_id = self.env['hr.contract'].search([('id', 'not in', self.ids),
                                                          ('employee_id', '=', rec.employee_id.id)],
                                                         order='date_start desc',
                                                         limit=1)
            if contract_id:
                date_start = datetime.strptime(contract_id.date_start, '%Y-%m-%d')
                date_end = datetime.strptime(contract_id.date_end, '%Y-%m-%d') if contract_id.date_end else ''
                start = datetime.strptime(rec.date_start, '%Y-%m-%d')

                err_msg = _('New contract overlap with contract ref %s (%s - %s)' % (contract_id.name,
                                                                                     contract_id.date_start,
                                                                                     contract_id.date_end if contract_id.date_end else 'unlimited'))

                if contract_id.date_end and (start <= date_start or start <= date_end):
                    raise ValidationError(err_msg)
                elif start <= date_start:
                    raise ValidationError(err_msg)
        return True

    # @api.model
    # def is_probation(self, employee_id = None):
    #     """
    #     Return employee probation status based on trial date start and end
    #     :param employee_id: id of employee
    #     :return: True if in probation
    #     """
    #     res = ''
    #
    #     # no contract no probation
    #     if employee_id:
    #         self = self.env['hr.contract'].search([('employee_id', '=', employee_id)],
    #                                               limit=1,
    #                                               order='date_start desc')
    #         if not self: return False
    #
    #     # trial dates is not mandatory
    #     if not self.trial_date_start or not self.trial_date_end: return False
    #
    #     today = datetime.today()
    #     trial_start = datetime.strptime(self.trial_date_start, '%Y-%m-%d')
    #     trial_end = datetime.strptime(self.trial_date_end, '%Y-%m-%d')
    #
    #     return True if trial_start <= today <= trial_end else False

    @api.model
    def current(self, employee, date=datetime.today(), period='year'):
        """
        Get contract of an employee based on today date and period.
        :param employee: employee recordset
        :param date: datetime
        :param period: month/year
        :return: contract recordset
        """
        today = date

        delta_period = {
            'month': [{'day': 1}, {'months': 1, 'day': 1, 'days': -1}],
            'year': [{'month': 1, 'day': 1}, {'month':12, 'months':1, 'day':1, 'days':-1}]
        }

        # use **dict to change into key=value format
        end = (today + relativedelta.relativedelta(**delta_period[period][1])).strftime(DF)

        # search all contract within the year
        contract_ids = self.env['hr.contract'].search([('employee_id', '=', employee.id),
                                                       ('date_start', '<=', end)],
                                                      order='date_start desc')

        for contract in contract_ids:
            if today.strftime(DF) >= contract.date_start:
                return contract

    @api.model
    def is_probation(self, date=None):
        """
        Check if a contract have probation time. Some mandor was at probation - required to be team leader and
        team member at the same time.
        :param date: datetime
        :return: True if mandor has probation
        """
        for contract in self:
            # stop if one of trial date empty
            if not contract.trial_date_start or not contract.trial_date_end:
                res = False
            else:
                # check probation based on today date.
                date_checked = datetime.today() if not date else date
                trial_start = datetime.strptime(self.trial_date_start, '%Y-%m-%d')
                trial_end = datetime.strptime(self.trial_date_end, '%Y-%m-%d')
                res = True if trial_start <= date_checked <= trial_end else False

            return res
