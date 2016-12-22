# -*- coding: utf-8 -*-

import logging
import pytz
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from math import floor
from rule_attendance import *

_logger = logging.getLogger(__name__)

class FingerAttendance(models.Model):
    """
    Saves AMS Solutions data. Each row creates attendance based on condition:
    1. Sign-in/out condition.
    2. Pengecualian condition (action reason).
    """
    _name = 'hr_fingerprint_ams.attendance'
    _description = 'Fingerprint Attendance'
    _rec_name = 'employee_name'

    db_id = fields.Integer('ID MDB')
    terminal_id = fields.Integer('Terminal ID')
    nik = fields.Char('NIK')
    employee_name = fields.Char('Employee Name')
    auto_assign = fields.Boolean('Auto Assign')
    date = fields.Date('Date')
    work_schedules = fields.Char('Working Schedule', help='Used to look up resource calendar.')
    time_start = fields.Float('Working Time Start', help='Time format in hh:mm')
    time_end = fields.Float('Working Time End', help='Time format in hh:mm')
    sign_in = fields.Float('Sign In', help='Time format in hh:mm')
    sign_out = fields.Float('Sign Out', help='Time format in hh:mm')
    day_normal = fields.Integer('Normal Day')
    day_finger = fields.Integer('Finger Day')
    hour_late = fields.Float('Late In', help='Time format in hh:mm')
    hour_early_leave = fields.Float('Early Out', help='Time format in hh:mm')
    absent = fields.Boolean('Absent')
    hour_overtime = fields.Float('Overtime', help='Time format in hh:mm')
    hour_work = fields.Float('Work Hour', help='Time format in hh:mm')
    action_reason = fields.Char('Action Reason', help='Attendance Action Desc')
    required_in = fields.Boolean('Required Sign In')
    required_out = fields.Boolean('Required Sign Out')
    department = fields.Char('Department')
    day_normal = fields.Integer('Normal Day')
    day_weekend = fields.Integer('Weekend Day')
    day_holiday = fields.Integer('Holiday')
    hour_attendance = fields.Float('Attendance Hour', help='Time format in hh:mm')
    hour_ot_normal = fields.Float('Overtime Hour', help='Time format in hh:mm')
    hour_ot_weekend = fields.Float('Weekend Work Hour', help='Time format in hh:mm')
    hour_ot_holiday = fields.Float('Holiday Work Hour', help='Time format in hh:mm')
    attendance_ids = fields.One2many('hr.attendance', 'finger_attendance_id', 'HR Attendance')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('approved', 'Approved'),
                              ('correction', 'Correction'),
                              ('payslip', 'Payslip'),
                              ('attendance', 'No Attendance Created')],
                             default='draft',
                             help='Import will update fingerprint attendance with draft state only.')

    @api.model
    def create(self, vals):
        """Create and update using same CSV format of fingerprint.
        Must meet attendance rule:
        1. Employee.
        2. Has sign-in.
        3. Has sign-out.
        """
        f_attendance_obj = self.env['hr_fingerprint_ams.attendance']

        # Update only when state is in draft
        current = f_attendance_obj.search([('db_id', '=', vals['db_id']),
                                           ('terminal_id', '=', vals['terminal_id']),
                                           ('employee_name', '=', vals['employee_name']),
                                           ('nik', '=', vals['nik']),
                                           ('date', '=', vals['date'])])
        # Override create should return a recordset
        res = self

        # Attendance constraints required complete sign-in and sign-out
        attendance = Attendance(self._get_employee(vals['employee_name'], vals['nik']),
                                vals['sign_in'],
                                vals['sign_out'])
        att_rule = AttendanceSpecification().\
            and_specification(EmployeeSpecification()).\
            and_specification(SignInSpecification()).\
            and_specification(SignOutSpecification())

        if att_rule.is_satisfied_by(attendance):
            if current:
                # Only update fingerprint attendance with draft status
                if current.state == 'draft':
                    update_vals = {
                        'sign_in': vals['sign_in'],
                        'sign_out': vals['sign_out']
                    }
                    current.write(update_vals)
                    res = current
                    self._create_attendance(res, vals, 'sign_in', True)
                    self._create_attendance(res, vals, 'sign_out', True)
            else:
                res = super(FingerAttendance, self).create(vals)
                self._create_attendance(res, vals)
                self._create_attendance(res, vals, 'sign_out')
        else:
            # Create non-fingerprint attendance (with action reason)
            action_reason_ids = self.env['hr.action.reason'].search([('active', '=', True),
                                                                     ('action_type', '=', 'action')])

            item = []
            for action_reason in action_reason_ids:
                item.append(action_reason['name'])

            if vals['action_reason'] in item:
                res = super(FingerAttendance, self).create(vals)
                self._create_attendance(res, vals, 'action')

            # if not vals['action_reason'] in set(item):
            #     # Ignore record which did not passed rules
            #     logger_msg = '%s attendance at %s did not satisfy attendance rule or registered action reason.' % (vals['employee_name'], vals['date'])
            #     _logger.warning(logger_msg)
            #     res = False
            # else:
            # print 'create attendance with action reason... sign_in %s and sign_out %s' % (
            # vals['time_start'], vals['time_end'])

        return res

    @api.model
    def _create_attendance(self, f_attendance, vals, action='sign_in', update=False):
        """
        Finger Attendance make use of HR Attendance.
        :param f_attendance: fingerprint attendance
        :param vals: data
        :param action: sign_in or sign_out
        :param update: set True for update action
        :return: instance of attendance
        """
        employee_id = self._get_employee(vals['employee_name'], vals['nik'])

        att_time = 0
        action_reason_id = None

        # define action and time
        if action == 'sign_in':
            att_time = vals['sign_in']
        elif action == 'sign_out':
            att_time = vals['sign_out']
        elif action == 'action':
            if vals['action_reason']:
                action_reason_id = self.env['hr.action.reason'].search([('active', '=', True),
                                                                        ('name', '=', vals['action_reason'])],
                                                                       limit=1).id

        att = {
            'finger_attendance_id': f_attendance.id,
            'employee_id': employee_id.id,
            'name': self._get_name(vals['date'], att_time),
            'action': action,
            'action_desc': action_reason_id,
        }

        if update:
            attendance_obj = self.env['hr.attendance']
            attendance_id = attendance_obj.search([('finger_attendance_id', '=', f_attendance.id),
                                                   ('action', '=', action)])
            res = attendance_id
            res.write(att)
        else:
            res = self.env['hr.attendance'].create(att)

        return res

    @api.multi
    def unlink(self):
        """
        Attendance follow Fingerprint
        :return:
        """
        for f_attendance in self:
            if f_attendance.state != 'draft':
                error_msg = _('You cannot delete approved Fingerprint records.')
                raise ValidationError(error_msg)

        return super(FingerAttendance, self).unlink()

    @api.model
    def _get_employee(self, employee_name, nik):
        """
        Need to check if imported data is an active registered employee or not.
        Args:
            employee_name: name
            employee_id: 10 digits employee registration number
        Returns: instance of an employee or false
        """
        ids = self.env['hr.employee'].search([('name', '=', employee_name),
                                              ('nik_number', '=', nik),
                                              ('active', '=', 1)])
        return ids and ids[0] or False

    @api.model
    def _get_name(self, att_date, att_time):
        """
        Attendance required datetime object
        :param att_date: fingerprint date
        :param att_time: fingerprint time
        :return: instance of datetime UTC
        """

        hour = int(floor(att_time))
        minute = int(round((att_time - hour) * 60))  # widget float_time use round
        second = '00'

        import_dt = datetime.strptime(att_date + ' ' + str(hour) + ':'
                                      + str(minute) + ':' + second, DT)

        # Odoo used UTC (timestamp without timezone).
        local = pytz.timezone(self._context['tz'])  # user timezone should match import time
        local_dt = local.localize(import_dt, is_dst=None)
        res = local_dt.astimezone(pytz.utc)

        return res

    @api.one
    def button_confirmed(self):
        self.write({
            'state': 'confirmed'
        })

    @api.one
    def button_approved(self):
        """Create analytic journal entry
        """
        self.write({
            'state': 'approved'
        })

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        """Remove sum of .
        """

        # No need to sum time_start, time_end, sign_in and sign_out
        if 'time_start' in fields:
            fields.remove('time_start')

        if 'time_end' in fields:
            fields.remove('time_end')

        if 'sign_in' in fields:
            fields.remove('sign_in')

        if 'sign_out' in fields:
            fields.remove('sign_out')

        return super(FingerAttendance, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby, lazy)

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    _description = 'Fingerprint Attendance Line'

    finger_attendance_id = fields.Many2one('hr_fingerprint_ams.attendance', ondelete='cascade')
    state = fields.Selection(related='finger_attendance_id.state', store=True)

    @api.model
    def get_attendance(self, employee, att_date, action='sign_in'):
        # Attendance saved in UTC
        local = pytz.timezone(self._context['tz'])
        date_from = datetime.strptime(att_date, DF)
        date_from_utc = local.localize(date_from, is_dst=None).astimezone(pytz.utc)
        date_to_utc = date_from_utc + timedelta(days=1)

        res = self.search([('employee_id', '=', employee.id),
                           ('action', '=', action),
                           ('name', '>=', date_from_utc.strftime(DT)),
                           ('name', '<=', date_to_utc.strftime(DT))])

        return res

    @api.multi
    @api.constrains('action')
    def _altern_si_so(self):
        """Support attendance with action type. Note: first attendance must be sign-in."""
        for record in self:
            if record.action == 'action':
                pass
            else:
                return super(HrAttendance, record)._altern_si_so()


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