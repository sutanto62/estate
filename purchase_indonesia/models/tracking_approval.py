from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re

class TrackingApproval(models.Model):

    _name = 'tracking.approval'
    _description = 'Tracking Approval for All Report Purchasing'

    name = fields.Char('Tracking Approval Name')
    owner_id = fields.Integer()
    state = fields.Char('State')
    datetime = fields.Datetime('Date and Time Approval')
    name_user = fields.Char('')