from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal
import time
import re


class MasterCalendarWorkday(models.Model):

    _name='master.calendar.effective.date'


    name = fields.Char(required=True)
    date_start = fields.Datetime()
    date_stop = fields.Datetime()
    agendaholiday_id = fields.Many2one('agenda.holiday','Agenda Holiday')
    hex_value = fields.Char(
        string="Hex Value",
        related="agendaholiday_id.color",
        store=False,
        size=7
    )

    #onchange
    @api.multi
    @api.onchange('name','agendaholiday_id')
    def _onchange_name(self):
        if self.agendaholiday_id:
            self.name = self.agendaholiday_id.name


class AgendaHoliday(models.Model):

    _name='agenda.holiday'

    name=fields.Char('Description Holiday')
    color=fields.Char('Choose Your Color',help='Choose Your Color')


