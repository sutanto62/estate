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


class InheritMaintenanceTask(models.Model):
    _inherit ='mro.task'
    _description = 'Add Field Type Task'

    typetask_id = fields.Many2one('estate.master.type.task')

    #onchange typetask_id :
    @api.multi
    @api.onchange('typetask_id')
    def _onchange_typetask_id(self):
        arrTypetask = []
        typetask = self.env['estate.master.type.task'].search([('parent_id','=',False)])
        for task in typetask:
            arrTypetask.append(task.id)
        return {
                'domain':{
                    'typetask_id' : [('id','in',arrTypetask)]
                }
            }