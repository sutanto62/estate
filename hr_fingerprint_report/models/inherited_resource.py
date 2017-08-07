# -*- coding: utf-8 -*-

import logging
import pytz
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from datetime import datetime, timedelta, time, date
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from math import floor
from decimal import *

_logger = logging.getLogger(__name__)

class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    @api.multi
    def get_day_work_from(self, date=None):
        """
        Get a day's hour from of today or certain date.
        :param date: datetime of day which work from time. If not given use today
        :type date: datetime
        :return: Attendance's work from
        :rtype: float
        """
        for record in self:
            attendance_ids = record.get_attendances_for_weekday(date or datetime.today())[0]

            if not attendance_ids:
                res = 0.0
                return res

            res = 24.0
            for att in attendance_ids:
                if att[0].hour_from < res:
                    res = att[0].hour_from

            return res

    @api.multi
    def get_day_work_to(self, date=None):
        """
        Get a day's hour to of today or certain date.
        :param date: datetime of day which work to time. If not given use today
        :type date: datetime
        :return: Attendance's work to
        :rtype: float
        """
        for record in self:
            attendance_ids = record.get_attendances_for_weekday(date or datetime.today())[0]

            if not attendance_ids:
                res = 0.0
                return res

            res = 0.0

            for att in attendance_ids:
                if att[0].hour_to > res:
                    res = att[0].hour_to

            return res

