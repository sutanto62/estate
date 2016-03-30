from openerp import models, fields, api, exceptions, _
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar


class inherit_blocktemplate():

    _inherit='estate.block.template'

    stage_id=fields.Many2one('estate.nursery.stage','Stage Nursery')

