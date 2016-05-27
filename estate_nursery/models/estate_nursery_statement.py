from openerp import models, fields, api, exceptions, _
from datetime import datetime, date
from openerp.exceptions import ValidationError

from dateutil.relativedelta import *
import calendar


class NurseryStatement(models.Model):

    _name = "estate.nursery.statement"

    name=fields.Char()
    batch_id = fields.Many2one('estate.nursery.batch')
    selection_id = fields.Many2one('estate.nursery.selection')
