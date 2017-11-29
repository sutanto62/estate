# -*- coding: utf-8 -*-

import logging
import pytz
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from math import floor
from decimal import *

_logger = logging.getLogger(__name__)

class FingerAttendance(models.Model):
    """
    Surrogate fields for export purposes. Make sure all attributes prefixed/suffixed. It required alter drop column
    at postgresql in order to recomputed employee_id, company_id, office_level_id, department_id, contract_type,
    contract_period, schedule_id and contract_id.
    to avoid overide parent attributes.
    """
    _name = 'hr_fingerprint_ams.attendance'
    _inherit = 'hr_fingerprint_ams.attendance'

    # integrate odoo, filter
    employee_id = fields.Many2one('hr.employee', 'Employee', compute='_compute_employee', store=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True)
    office_level_id = fields.Many2one(related='employee_id.office_level_id', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True)
    contract_type = fields.Selection([('1', 'PKWTT'), ('2', 'PKWT')], related='employee_id.contract_type', store=True)
    contract_period = fields.Selection([('1', 'Monthly'), ('2', 'Daily')], related='employee_id.contract_period', store=True)
    schedule_id = fields.Many2one(related='contract_id.working_hours',
                                  help='Help to get time start and time end.', store=True)
    contract_id = fields.Many2one('hr.contract', 'Contract', compute='_compute_employee',
                                  help='Working schedule might be updated based on contract.', store=True)

    # surrogate
    db_id_c = fields.Char('Emp No.', compute='_compute_pivot')
    terminal_id_c = fields.Char('No. ID', compute='_compute_pivot')
    employee_name_c = fields.Char('Nama', compute='_compute_pivot')
    date_c = fields.Char('Tanggal', compute='_compute_pivot')
    work_schedules_c = fields.Char('Jam Kerja', compute='_compute_pivot')
    sign_in_t = fields.Char('Scan Masuk', compute='_compute_time')
    sign_out_t = fields.Char('Scan Pulang', compute='_compute_time')
    time_start_t = fields.Char('Jam Masuk', compute='_compute_time')
    time_end_t = fields.Char('Jam Pulang', compute='_compute_time')
    action_reason_c = fields.Char('Pengecualian', compute='_compute_pivot')
    day_normal_c = fields.Char('Normal', compute='_compute_pivot')
    day_finger_c = fields.Char('Riil', compute='_compute_pivot')
    day_weekday_c = fields.Char('Hari Normal', compute='_compute_pivot')
    day_weekend_c = fields.Char('Akhir Pekan', compute='_compute_pivot')
    day_holiday_c = fields.Char('Hari Libur', compute='_compute_pivot')
    required_in_c = fields.Char('Harus C/In')
    required_out_c = fields.Char('Harus C/Out')

    hour_late_t = fields.Char('Terlambat', compute='_compute_time')
    hour_early_leave_t = fields.Char('Plg. Cepat', compute='_compute_time')
    hour_overtime_t = fields.Char('Lembur', compute='_compute_time')
    hour_work_t = fields.Char('Jml Jam Kerja', compute='_compute_time')
    hour_attendance_t = fields.Char('Jml Kehadiran', compute='_compute_time')
    hour_ot_normal_t = fields.Char('Lembur Hari Normal', compute='_compute_time')
    hour_ot_weekend_t = fields.Char('Lembur Akhir Pekan', compute='_compute_time')
    hour_ot_holiday_t = fields.Char('Lembur Hari Libur', compute='_compute_time')
    # hour_early_leave_t = fields.Char('Plg. Cepat', compute='_compute_time')

    # pivot required, string should match pivot source data column name
    p_year = fields.Integer('YEAR', compute='_compute_pivot')
    p_month = fields.Integer('MONTH', compute='_compute_pivot')
    p_week = fields.Integer('WEEK', compute='_compute_pivot')
    p_date = fields.Integer('DATE', compute='_compute_pivot')
    p_day_normal = fields.Integer('NORMAL HARI KERJA', compute='_compute_pivot')
    p_day_finger = fields.Integer('RILL HARI KERJA', compute='_compute_pivot')
    p_hour_late = fields.Float('TERLAMBAT (MNT) Source', compute='_compute_pivot', search='_search_hour_late)')
    p_hour_late_office = fields.Integer('Terlambat (MNT) Kary Kantor', compute='_compute_pivot', search='_search_hour_late_office')
    p_late_amount = fields.Integer('TERLAMBAT (X) Source', compute='_compute_pivot', search='_search_late_amount')
    p_late_amount_office = fields.Integer('Terlambat (X) Kary Kantor', compute='_compute_pivot')
    p_early_leave_leave = fields.Float('PLG CEPAT (MNT)', compute='_compute_pivot')
    p_early_leave = fields.Integer('PLG Cepat Source', compute='_compute_pivot')
    p_hour_early_leave = fields.Integer('PLG CEPAT ALL (MNT)', compute='_compute_pivot')
    p_early_leave_amount = fields.Integer('PLG CEPAT (X) Source', compute='_compute_pivot')
    p_labor_early_leave = fields.Integer('CPLG CEPAT ALL (X)', compute='_compute_pivot')
    p_absent = fields.Integer('ABSEN', compute='_compute_pivot')
    p_leave = fields.Integer('CUTI', compute='_compute_pivot')
    p_sick = fields.Integer('SAKIT', compute='_compute_pivot')
    p_permit = fields.Integer('IJIN', compute='_compute_pivot')
    p_business_trip = fields.Integer('DINAS LUAR', compute='_compute_pivot')
    p_out_office = fields.Integer('KELUAR KANTOR', compute='_compute_pivot')
    p_no_reason = fields.Integer('MANGKIR', compute='_compute_pivot')
    p_n_sign_in = fields.Integer('N/CLOCK IN', compute='_compute_pivot')
    p_n_percent_in = fields.Integer('PERCENT N/CIN', compute='_compute_pivot')
    p_n_sign_out = fields.Integer('N/ CLOCK OUT', compute='_compute_pivot')
    p_n_percent_out = fields.Integer('PERCENT N/COUT', compute='_compute_pivot')
    p_n_sign_in_out = fields.Integer('N CLOCK IN/OUT', compute='_compute_pivot')
    p_n_percent_in_out = fields.Integer('PERCENT N CLOCK IN/OUT', compute='_compute_pivot')
    p_sign_in_amount = fields.Integer('SCAN MASUK(X)', compute='_compute_pivot')
    p_sign_out_amount = fields.Integer('SCAN PULANG (X)', compute='_compute_pivot')
    p_sign_amount = fields.Integer('JUMLAH SCAN', compute='_compute_pivot')
    p_sign_percent = fields.Integer('PERSEN SCAN', compute='_compute_pivot')
    p_hour_work = fields.Float('JUMLAH JAM KERJA', compute='_compute_pivot')
    p_hour_attendance = fields.Float('JML JAM KEHADIRAN', compute='_compute_pivot')
    p_hour_work_float = fields.Float('JML Jam Kerja (Jam)', compute='_compute_pivot')
    p_hour_attendance_float = fields.Float('JML Kehadiran (Jam)', compute='_compute_pivot')
    p_average_day_work = fields.Integer('RATA-RATA', compute='_compute_pivot')
    p_days = fields.Char('DAYS', compute='_compute_pivot')
    p_labor_late_circle = fields.Integer('Terlambat Menit KHL (Apel)', compute='_compute_pivot')
    p_labor_late_circle_amount = fields.Integer('Terlambat X KHL Apel', compute='_compute_pivot')
    p_estate_late = fields.Integer('Terlambat Menit Kebun', compute='_compute_pivot')
    p_estate_late_amount = fields.Integer('Terlambat X Kebun', compute='_compute_pivot')
    p_labor_late = fields.Integer('Terlambat Menit KHL Kerja', compute='_compute_pivot')
    p_labor_late_amount = fields.Integer('Terlambat X KHL Kerja', compute='_compute_pivot')
    p_action_reason = fields.Char('Pengecualian4', compute='_compute_pivot')
    p_late_all = fields.Integer('Terlambat All3', compute='_compute_pivot')
    p_no_reason_all = fields.Integer('Mangkir22', compute='_compute_pivot')
    p_piece_rate_day = fields.Integer('Premi HK2', compute='_compute_pivot')
    p_scan_hour = fields.Float('Jml Jam Kehadiran (Scan)', compute='_compute_pivot')
    p_scan_day_finger = fields.Float('Rill Hari Kerja (Scan)', compute='_compute_pivot')

    @api.multi
    @api.depends('employee_name', 'nik', 'date')
    def _compute_employee(self):
        """ Employee might have different work schedules based on contract."""
        for record in self:
            employee_obj = self.env['hr.employee']
            employee_id = employee_obj.search([('name_related', '=', record.employee_name),
                                               ('nik_number', '=', record.nik)], limit=1)

            # make sure to get latest contract
            contract_id = self.env['hr.contract'].search([('employee_id', '=', employee_id.id),
                                                          ('date_start', '<=', record.date),
                                                          ('date_end', '>=', record.date)],
                                                         order='date_end desc',
                                                         limit=1)
            record.employee_id = employee_id.id
            record.contract_id = contract_id.id
            record.contract_period = employee_id.contract_period
            record.contract_type = employee_id.contract_type
            record.company_id = employee_id.company_id.id
        return True

    @api.multi
    def _update(self):
        """ Wrapper for _compute_time and _compute_pivot"""
        for record in self:
            record._compute_employee()
            record._compute_time()
            record._compute_pivot()
            return True

    @api.multi
    def _compute_time(self):
        """ Export purposes"""
        for record in self:
            date = datetime.strptime(record.date, DF)

            # Required data cleansing
            # hour_from = record.schedule_id.get_day_work_from(date)
            # hour_to = record.schedule_id.get_day_work_to(date)

            record.sign_in_t = record.float_to_datetime(record.sign_in)
            record.sign_out_t = record.float_to_datetime(record.sign_out)
            record.time_start_t = str(record.float_to_datetime(record.time_start))
            record.time_end_t = str(record.float_to_datetime(record.time_end))
            record.hour_late_t = record.float_to_datetime(record.hour_late)
            record.hour_early_leave_t = record.float_to_datetime(record.hour_early_leave)
            record.hour_overtime_t = record.float_to_datetime(record.hour_overtime)
            record.hour_work_t = record.float_to_datetime(record.hour_work)
            record.hour_attendance_t = record.float_to_datetime(record.hour_attendance)
            record.hour_ot_normal_t = record.hour_ot_normal if record.hour_ot_normal > 0 else ''
            record.hour_ot_weekend_t = record.hour_ot_weekend if record.hour_ot_weekend > 0 else ''
            record.hour_ot_holiday_t = record.hour_ot_holiday if record.hour_ot_holiday > 0 else ''
            # record.hour_early_leave_t = record.float_to_datetime(record.hour_early_leave)
        return True

    @api.multi
    def _compute_pivot(self):
        """ Export purposes."""
        getcontext().prec = 8
        for record in self:
            date = datetime.strptime(record.date, DF)
            date_day = date.strftime('%A')

            # Convert to char
            record.db_id_c = str(record.db_id)
            record.terminal_id_c = str(record.terminal_id)
            record.employee_name_c = record.employee_name
            record.date_c = str(date.strftime('%m/%d/%Y'))
            record.work_schedules_c = record.work_schedules
            record.day_normal_c = str(record.day_normal)
            record.day_finger_c = str(record.day_finger)
            record.day_weekday_c = '1' if date.isoweekday() > 0 else ''
            record.day_weekend_c = '1' if date.isoweekday() == 7 else ''
            record.day_holiday_c = str(record.day_holiday) if record.day_holiday > 0 else ''
            record.required_in_c = 'True' if record.required_in else 'False'
            record.required_out_c = 'True' if record.required_out else 'False'
            record.action_reason_c = record.action_reason if record.action_reason else ''

            record.p_year = date.strftime('%Y')
            record.p_month = date.strftime('%m')
            # %U as Sunday is the first day of the week
            record.p_week = date.strftime('%U')
            record.p_date = date.strftime('%d')
            record.p_day_normal = 0 if str(record.nik)[:1] == '3' and record.day_finger == 0 else record.day_normal
            record.p_day_finger = 0 if record.day_finger == '' or record.day_finger == 0 else record.day_finger
            record.p_hour_late = record.timevalue(record.hour_late_t)
            t = Decimal(record.p_hour_late) * Decimal(24) * Decimal(60)
            record.p_hour_late_office = round(t,0) if record.work_schedules in ('RO SenJum', 'RO Sabtu', 'Sec Pagi', 'Sec Malam', 'Staff HO') else 0
            record.p_late_amount = 1 if record.p_hour_late_office else 0
            record.p_late_amount_office = 1 if (record.work_schedules in ('RO SenJum', 'RO Sabtu', 'Staff HO')) and record.p_hour_late_office >= 5 else 0
            record.p_early_leave_leave = record.timevalue(record.hour_early_leave_t)
            c = Decimal(record.p_early_leave_leave) * Decimal(24) * Decimal(60)
            record.p_early_leave = round(c,0)
            record.p_hour_early_leave = record.get_early_leave(record.sign_out)
            record.p_early_leave_amount = 1 if (record.action_reason == 'Pulang Cepat') or (record.p_hour_early_leave > 0) else 0
            # p_labor_early_leave not required
            # record.p_labor_early_leave = record.p_early_leave_amount if record.nik[:1] != '3' and record.p_days not in ('Friday', 'Saturday') else 0
            absent = record.day_normal - record.day_finger
            record.p_absent = absent if absent > 0 else 0
            record.p_leave = 1 if record.action_reason == 'Cuti' else 0
            record.p_sick = 1 if record.action_reason == 'Sakit' else 0
            record.p_permit = 1 if record.action_reason == 'Ijin' else 0
            record.p_business_trip = 1 if record.action_reason == 'Dinas Luar' else 0
            record.p_out_office = 1 if record.action_reason == 'Keluar Kantor' else 0
            record.p_no_reason = 1 if record.nik[:1] in ('1', '2') and record.absent and record.action_reason == '' else 0
            record.p_n_sign_in = 1 if not record.sign_in and record.action_reason not in ('Cuti', 'Dinas Luar') else 0
            record.p_n_percent_in = 0 if record.p_n_sign_in == 0 else 100
            record.p_n_sign_out = 1 if not record.sign_out and record.action_reason not in ('Cuti', 'Dinas Luar') else 0
            record.p_n_percent_out = 0 if record.p_n_sign_out == 0 else 100
            record.p_n_sign_in_out = 1 if not record.sign_in and not record.sign_out else 0
            record.p_n_percent_in_out = (record.p_n_percent_in + record.p_n_percent_out)/2
            record.p_sign_in_amount = 1 if record.sign_in or record.action_reason in ('Cuti', 'Sakit', 'Ijin', 'Dinas Luar') else 0
            record.p_sign_out_amount = 1 if record.sign_out or record.action_reason in ('Cuti', 'Sakit', 'Ijin', 'Dinas Luar') else 0
            record.p_sign_amount = record.p_sign_in_amount + record.p_sign_out_amount
            if record.nik[:1] in ('1', '2'):
                avgpercent = (record.p_sign_in_amount*50) + (record.p_sign_out_amount*50)
            elif record.nik[:1] == '3':
                if record.p_sign_in_amount and record.p_sign_in_amount:
                    avgpercent = 100
                else:
                    avgpercent = 0
            record.p_sign_percent = avgpercent
            record.p_hour_work = record.timevalue(record.hour_work_t)
            record.p_hour_attendance = record.timevalue(record.hour_attendance_t) if record.hour_attendance_t else 0
            record.p_hour_work_float = round(Decimal(record.p_hour_work)*Decimal(24), 2)
            record.p_hour_attendance_float = round(Decimal(record.p_hour_attendance)*Decimal(24), 2)
            try:
                avgdaywork = (record.p_day_finger/record.p_day_normal)*100
            except ZeroDivisionError:
                avgdaywork = 0
            record.p_average_day_work = 100 if record.nik[:1] == '3' else avgdaywork
            record.p_days = date_day
            labor_late = Decimal(record.p_hour_late)*Decimal(24)*Decimal(60)
            record.p_labor_late_circle = labor_late if record.nik[:1] == '3' and record.work_schedules in ('Opr Kebun SenSab', 'Opr Kebun Jumat') else 0
            record.p_labor_late_circle_amount = 1 if record.p_labor_late_circle >= 1 else 0
            record.p_estate_late = labor_late if record.nik[:1] in ('1', '2') and record.work_schedules in ('Opr Kebun SenSab', 'Opr Kebun Jumat', 'Waker Pagi', 'Waker Malam') else 0
            record.p_estate_late_amount = 1 if record.p_estate_late >= 1 else 0
            record.p_labor_late = record.p_labor_late_circle - 30 if record.p_labor_late_circle > 30 else 0
            record.p_labor_late_amount = 1 if record.p_labor_late >= 1 else 0

            reason = ''
            if record.p_labor_early_leave:
                reason = 'Pulang Cepat'
            elif record.p_late_amount_office:
                reason = 'Terlambat'
            elif record.p_estate_late_amount:
                reason = 'Terlambat'
            elif record.p_labor_late_amount:
                reason = 'Terlambat'
            elif record.p_no_reason:
                reason = 'Mangkir'
            elif record.p_leave:
                reason = 'Cuti'
            elif record.p_sick:
                reason = 'Sakit'
            elif record.p_business_trip:
                reason = 'Dinas Luar'
            elif record.p_out_office:
                reason = 'Keluar Kantor'
            elif record.p_permit:
                reason = 'Ijin'
            else:
                reason = ''
            record.p_action_reason = reason

            record.p_late_all = 1 if record.p_estate_late_amount or record.p_labor_late_amount or record.p_late_amount_office else 0
            record.p_no_reason_all = 1 if record.p_action_reason == 'Mangkir' else 0
            record.p_piece_rate_day = 0 if record.p_action_reason in ('Cuti', 'Ijin', 'Sakit', 'Dinas Luar','Mangkir') else record.p_day_finger
            record.p_scan_hour = record.sign_out - record.sign_in if record.sign_in and record.sign_out else 0
            record.p_scan_day_finger = record.p_scan_hour/record.p_hour_work_float if record.p_hour_work_float else 0


        return True

    def _get_time(self, schedule, date, mode=1):
        """
        Working schedules should follow employee contract.
        :param schedule: working schedules as written at employee contract
        :param date: fingerprint date
        :param mode: 1 is check time start, 2 is time end
        :return: char: earliest/latest time
        """
        day = datetime.strptime(date, DF)
        att_obj = self.env['resource.calendar.attendance']

        if mode == 1:
            order = 'hour_from asc'
        elif mode == 2:
            order = 'hour_to desc'

        att_id = att_obj.search([('calendar_id', '=', schedule.id),
                                 ('dayofweek', '=', day.weekday())],
                                order=order,
                                limit=1)

        if mode == 1:
            res = att_id.hour_from
        elif mode == 2:
            res = att_id.hour_to

        return res

    def float_to_datetime(self, val):
        """
        Refactoring. Pivot required char.
        :param val: time in float
        :return: time format
        """
        if val:
            float_time = abs(val)
            return '{0:02.0f}:{1:02.0f}'.format(*divmod(float_time * 60, 60))
        else:
            return False

    def timevalue(self, string):
        """ Excel used timevalue to display duration."""
        if not string:
            return '0'
        t = string
        (h, m) = t.split(':')

        # Excel timevalue precision 8
        getcontext().prec = 8
        decimal_t = Decimal((int(h)*60) + int(m))
        decimal_d = Decimal(int(24)*60)
        res = decimal_t/decimal_d
        return res

    @api.multi
    def get_early_leave(self, sign_out):
        """
        Return integer of early leave
        :param sign_out: sign out datetime
        :type sign_out: float
        :return: minutes of early leave
        :rtype: integer
        """
        for record in self:
            finger_date = datetime.strptime(record.date, DF)
            finger_day = finger_date.strftime('%A')
            is_pkwt_daily = True if record.nik[:1] == '3' else False
            schedule = record.work_schedules

            # todo should switch to res_calendar
            time_end = {
                'Friday': 11.0,
                'Saturday': 13.0
            }

            res = 0
            if is_pkwt_daily and finger_day == 'Friday' and schedule == 'Opr Kebun SenSab':
                # PKWT Daily at site
                delta = time_end['Friday'] - record.sign_out
                res = int(round(delta, 2) * 60)
            elif is_pkwt_daily and finger_day == 'Saturday' and schedule == 'RO SenJum':
                # PKWT Daily at site office
                delta = time_end['Saturday'] - record.sign_out
                res = int(round(delta, 2) * 60)
            else:
                # Other did not required recalculation
                res = record.p_early_leave
            return res if res > 0 else 0

    def _search_hour_late(self, operator, value):
        if operator == 'like':
            operator = 'ilike'
        return [('p_hour_late', operator, value)]

    def _search_late_amount(self, operator, value):
        if operator == 'like':
            operator = 'ilike'
        return [('p_late_amount', operator, value)]

    def _search_hour_late_office(self, operator, value):
        if operator == 'like':
            operator = 'ilike'
        return [('p_hour_late_office', operator, value)]
