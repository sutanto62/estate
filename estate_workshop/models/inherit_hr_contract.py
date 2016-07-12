from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
import time
import datetime
from openerp import tools

class InheritHrContract(models.Model):

    _inherit = 'hr.contract'

    weekly_wage = fields.Float(readonly=False)
    daily_wage = fields.Float(readonly=False)
    hourly_wage = fields.Float(readonly=False)
    day = fields.Float()
    hour = fields.Float()
    active = fields.Boolean('Contract Active',defaults=False)

    #Onchange
    @api.multi
    @api.onchange('wage','weekly_wage','daily_wage','hourly_wage','day','hour')
    def _onchange_wage(self):
        if self.wage and self.hour and self.day:
            self.weekly_wage = self.wage/int(4)
            self.daily_wage = self.weekly_wage/float(self.day)
            self.hourly_wage = self.daily_wage/float(self.hour)

    @api.multi
    @api.constrains('day','hour')
    def _constraint_day_hour(self):
        for dayandhour in self.read(['day','hour']):
            if dayandhour['day'] and dayandhour['hour'] <= 0 :
                error_msg = "Day and Hour Field Must be Filled"
                raise exceptions.ValidationError(error_msg)
            elif dayandhour['day'] <= 0 :
                error_msg = "Day Field Must be Filled"
                raise exceptions.ValidationError(error_msg)
            elif dayandhour['hour'] <= 0 :
                error_msg = "Hour Field Must be Filled"
                raise exceptions.ValidationError(error_msg)
            elif dayandhour['hour'] > 24 :
                error_msg = "Hour Field not More Than 24 Hour"
                raise exceptions.ValidationError(error_msg)
                return False
        return True

    @api.multi
    @api.constrains('working_hours')
    def _constraint_workinghours(self):
        for workingHours in self:
            if workingHours.working_hours.id != True :
                error_msg = "Working Hours Field Must be Filled"
                raise exceptions.ValidationError(error_msg)
                return False
        return True