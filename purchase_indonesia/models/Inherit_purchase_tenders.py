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


class InheritPurchaseTenders(models.Model):

    _inherit = 'purchase.requisition'


    type_location = fields.Selection([('estate','Estate'),
                                     ('ho','HO'),('ro','RO')],'Location Type')