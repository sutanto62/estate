# -*- coding: utf-8 -*-

import logging
import pytz
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from math import floor
from rule_attendance import *

_logger = logging.getLogger(__name__)

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    _description = 'Fingerprint Attendance Line'

    finger_attendance_id = fields.Many2one('hr_fingerprint_ams.attendance', ondelete='cascade')
    state = fields.Selection(related='finger_attendance_id.state', store=True)

    def _altern_si_so(self, cr, uid, ids, context=None):
        """ Implementing this logic must be in old api. Using new api will not overide inheritance method"""

        for att in self.browse(cr, uid, ids, context=context):
            # bypass super to allow insert old record
            if att.action == 'action' or att.action == 'sign_in' or att.action == 'sign_out':
                return True
            else:
                return super(HrAttendance, self)._altern_si_so(cr, uid, ids, context)

    _constraints = [(_altern_si_so, 'Error ! Sign in (resp. Sign out) must follow Sign out (resp. Sign in)', ['action'])]

    @api.model
    def get_attendance(self, employee, att_date, action='sign_in'):
        """
        Return attendance record based on action
        Args:
            employee: employee
            att_date: date of attendance
            action: attendance action reason

        Returns: single attendance

        """
        # Attendance saved in UTC
        local = pytz.timezone(self._context['tz'])
        date_from = datetime.strptime(att_date, DF)
        date_from_utc = local.localize(date_from, is_dst=None).astimezone(pytz.utc)
        date_to_utc = date_from_utc + timedelta(days=1)

        # make sure only return one recordset
        res = self.search([('employee_id', '=', employee.id),
                           ('action', '=', action),
                           ('name', '>=', date_from_utc.strftime(DT)),
                           ('name', '<=', date_to_utc.strftime(DT))],
                          limit=1)

        return res


class ActionReason(models.Model):
    """Some fingerprint has action reason that replace sign-in/out. Such as Sakit/Cuti/Dinas Luar"""
    _inherit = 'hr.action.reason'

    # Overide inherit action_type selection
    # action_type = fields.Selection([('action', 'Action'),('sign_in', 'Sign in'), ('sign_out', 'Sign out')], "Action Type"),
    contract_type = fields.Selection([('1', 'PKWTT'), ('2', 'PKWT')], "Contract Type",
                                     help="* PKWTT, Perjanjian Kerja Waktu Tidak Tertentu, " \
                                          "* PKWT, Perjanjian Kerja Waktu Tertentu.")
    contract_period = fields.Selection([('1', 'Monthly'), ('2', 'Daily')], "Contract Period",
                                       help="* Monthly, Karyawan Bulanan, " \
                                            "* Daily, Karyawan Harian.")
    active = fields.Boolean('Active', default=True)