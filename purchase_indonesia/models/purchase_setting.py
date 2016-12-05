from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re


class PurchaseType(models.Model):

    _name = 'purchase.indonesia.type'
    _description = 'Setting type Purchase'

    name = fields.Char('Name')
    max_days = fields.Integer('Max Days')
    min_days = fields.Integer('Min Days')

class PurchaseParams(models.Model):

    _name ='purchase.params.setting'

    name = fields.Char('Object Name',required=True)
    value_params = fields.Text('Value')