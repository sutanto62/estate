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


class TaskMaintenanceOrder(models.Model):

    _name = 'task.maintenance.order'
    _description = 'Parent Task Maintenance Order'

    name=fields.Char('Task')
    mastertask_id = fields.Many2one('estate.workshop.mastertask',store=True)
    mro_id = fields.Many2one('mro.order','MRO',store=True)
    owner_id = fields.Integer('Owner')
    planned_hour =fields.Float('Planned Hour',store=True,readonly=True)
    planned_manpower = fields.Float('Planned Manpower',store=True,readonly=True)
    actual_hour = fields.Float('Actual Hour',store=True,readonly=True)
    actual_manpower = fields.Float('Actual Manpower',store=True,readonly=True)

class ActualTask(models.Model):

    _name = 'estate.workshop.actualtask'
    _inherits = {'task.maintenance.order':'parenttask_id'}
    _description = 'Actual Task'

    name = fields.Char('Actual Task')
    mro_id = fields.Many2one('mro.order','MRO',store=True)
    parenttask_id = fields.Many2one('task.maintenance.order',required=True,ondelete='cascade')

    @api.one
    @api.onchange('planned_hour','planned_manpower','mastertask_id')
    def _onchange_actualhour_actualmainpower(self):
        if self.mastertask_id:
            self.planned_hour = self.env['estate.workshop.mastertask'].search([('id','=',self.mastertask_id.id)]).planned_hour
            self.planned_manpower = self.env['estate.workshop.mastertask'].search([('id','=',self.mastertask_id.id)]).planned_manpower
        return True

    @api.multi
    @api.onchange('mastertask_id','owner_id','asset_id','mro_id')
    def _onchange_mastertask_id(self):
        arrOrder = []
       #todo onchange mastertask id tanpa di menunggu mro order tersimpan
        self.owner_id = self.mro_id.owner_id
        if self:
            return {
                'domain':{
                    'mastertask_id' : [('asset_id.id','=',self.owner_id)]
                }
            }

class PlannedTask(models.Model):

    _name = 'estate.workshop.plannedtask'
    _inherits = {'task.maintenance.order':'parenttask_id'}

    name = fields.Char('Planned Task')
    mro_id = fields.Many2one('mro.order','MRO',store=True)
    parenttask_id = fields.Many2one('task.maintenance.order',required=True,ondelete='cascade')

    # # #onchange planned hour and manpower
    @api.one
    @api.onchange('planned_hour','planned_manpower','mastertask_id')
    def _onchange_plannedhour_plannedmainpower(self):
        if self.mastertask_id:
            planned_hour = self.env['estate.workshop.mastertask'].search([('id','=',self.mastertask_id.id)]).planned_hour
            planned_manpower = self.env['estate.workshop.mastertask'].search([('id','=',self.mastertask_id.id)]).planned_manpower
            self.planned_hour = planned_hour
            self.planned_manpower = planned_manpower
        return True


    @api.multi
    @api.onchange('mastertask_id','owner_id','asset_id','mro_id')
    def _onchange_planmastertask_id(self):
        arrOrder = []
       #todo onchange mastertask id tanpa di menunggu mro order tersimpan
        self.owner_id = self.mro_id.owner_id
        if self:
            return {
                'domain':{
                    'mastertask_id' : [('asset_id.id','=',self.owner_id)]
                }
            }
