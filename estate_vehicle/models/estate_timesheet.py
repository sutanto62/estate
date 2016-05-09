from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar


class MasterTimesheet(models.Model):

    _name = 'estate.timesheet'
    _description = "Estate Master Time Sheet for Activity"

class TimesheetActivityTransport(models.Model):

    _name = 'estate.timesheet.activity.transport'
    _description = "Estate Master Time Sheet for Activity Transport"

    name=fields.Char("Timesheet Activity Tranport")
    date_activity_transport = fields.Date("Date activity Transport")
    employee_id = fields.Many2one('')

