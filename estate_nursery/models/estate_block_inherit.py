from openerp import models, fields, api, exceptions, _
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar


class inherit_blocktemplate():
    #inherit stage_id to location for search location where stage_id

    _inherit='estate.block.template'

    stage_id=fields.Many2one('estate.nursery.stage','Stage Nursery')

