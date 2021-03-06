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
    category_unit_id = fields.Many2one('master.category.unit','Category')

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

    @api.multi
    @api.onchange('category_unit_id','asset_id')
    def _onchange_category_unit_id(self):
        for record in self:
            if record.asset_id:
                record.category_unit_id = record.asset_id.category_unit_id

    @api.multi
    @api.onchange('asset_id','category_unit_id')
    def _onchange_asset_id(self):
        arrAsset = []
        for record in self:
            if record.category_unit_id:
                temp = record.env['asset.asset'].search([('category_unit_id','=',record.category_unit_id.id)])
                for asset in temp:
                    arrAsset.append(asset.id)
                return {
                'domain':{
                    'asset_id' : [('id','in',arrAsset)]
                }
            }