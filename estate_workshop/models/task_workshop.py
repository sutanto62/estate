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
    mastertasklineactual_ids = fields.One2many('v.task.mro.order.actual','ewa_id','Maintenance Task')
    parttasklineactual_ids = fields.One2many('v.actual.parts.task','ewa_id','Part Task')

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
        self.owner_id = self.mro_id.category_unit_id
        if self:
            return {
                'domain':{
                    'mastertask_id' : [('category_unit_id.id','=',self.owner_id)]
                }
            }

class PlannedTask(models.Model):

    _name = 'estate.workshop.plannedtask'
    _inherits = {'task.maintenance.order':'parenttask_id'}

    name = fields.Char('Planned Task')
    mro_id = fields.Many2one('mro.order','MRO',store=True)
    parenttask_id = fields.Many2one('task.maintenance.order',required=True,ondelete='cascade')
    mastertaskline_ids = fields.One2many('v.task.mro.order','ewp_id','Maintenance Task')
    parttaskline_ids = fields.One2many('v.planned.parts.task','ewp_id','Parts Task')

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
        self.owner_id = self.mro_id.category_unit_id
        if self:
            return {
                'domain':{
                    'mastertask_id' : [('category_unit_id.id','=',self.owner_id)]
                }
            }

class ViewTaskMroOrderPlanned(models.Model):

    _name = 'v.task.mro.order'
    _description = "Planned Task Pop up for vehicle"
    _auto = False
    _order='ewp_id'

    id = fields.Integer()
    ewp_id = fields.Many2one('estate.workshop.plannedtask')
    ewm_id = fields.Many2one('estate.workshop.mastertaskline')
    task_id = fields.Many2one('mro.task')
    mro_id = fields.Many2one('mro.id')

    def init(self, cr):
        cr.execute("""create or replace view v_task_mro_order as
                    select row_number() over()id,
                        ewp_id,
                        ewm.id as ewm_id,mro_id ,
                        task_id,mtask.mastertask_id as mastertask_id
                        from
                            estate_workshop_mastertaskline ewm
                        inner join (
                             select ewp.mro_id mro_id,ewp.id as ewp_id,mastertask_id
                                from
                                    estate_workshop_plannedtask ewp
                                inner join
                                    task_maintenance_order tmo on ewp.parenttask_id = tmo.id
                            )mtask
                            on
                                ewm.mastertask_id = mtask.mastertask_id
                            group by
                                ewm_id,mro_id,mtask.mastertask_id,task_id,ewp_id
                            order by mro_id,ewm_id asc""")

class ViewTaskMroOrderActual(models.Model):

    _name = 'v.task.mro.order.actual'
    _description = "Actual Task Pop up for vehicle"
    _auto = False
    _order='ewa_id'

    id = fields.Integer()
    ewa_id = fields.Many2one('estate.workshop.actualtask')
    ewm_id = fields.Many2one('estate.workshop.mastertaskline')
    task_id = fields.Many2one('mro.task')
    mro_id = fields.Many2one('mro.id')

    def init(self, cr):
        cr.execute("""create or replace view v_task_mro_order_actual as
                select row_number() over()id,
                    ewa_id,
                    ewm.id as ewm_id,mro_id ,
                    task_id,
                    mtask.mastertask_id as mastertask_id
                    from
                        estate_workshop_mastertaskline ewm
                    inner join (
                         select ewa.mro_id mro_id,ewa.id as ewa_id,mastertask_id
                            from
                                estate_workshop_actualtask ewa
                            inner join
                                task_maintenance_order tmo on ewa.parenttask_id = tmo.id
                        )mtask
                        on
                            ewm.mastertask_id = mtask.mastertask_id
                        group by
                            ewm_id,mro_id,mtask.mastertask_id,task_id,ewa_id
                        order by mro_id,ewm_id asc""")

class ViewPlannedPartsTask(models.Model):

    _name = 'v.planned.parts.task'
    _description = "Planned Part Task Pop up for vehicle"
    _auto = False
    _order='ewp_id'

    id = fields.Integer()
    ewp_id = fields.Many2one('estate.workshop.plannedtask')
    ewm_id = fields.Many2one('estate.workshop.mastertaskline')
    task_id = fields.Many2one('mro.task')
    mro_id = fields.Many2one('mro.id')
    parts_id = fields.Many2one('product.product')
    parts_uom = fields.Many2one('product.uom')
    parts_qty = fields.Float('Parts QTY')

    def init(self, cr):
        cr.execute("""create or replace view v_planned_parts_task as
                        select row_number() over()id,
                            ewp_id,parts_id,parts_uom,parts_qty,
                            ewm_id,mro_id ,
                            vtmo.task_id,mastertask_id from mro_task_parts_line mtpl
                        right join v_task_mro_order vtmo on vtmo.task_id = mtpl.task_id""")

class ViewActualPartsTask(models.Model):

    _name = 'v.actual.parts.task'
    _description = "Actual Part Task Pop up for vehicle"
    _auto = False
    _order='ewa_id'

    id = fields.Integer()
    ewa_id = fields.Many2one('estate.workshop.actualtask')
    ewm_id = fields.Many2one('estate.workshop.mastertaskline')
    task_id = fields.Many2one('mro.task')
    mro_id = fields.Many2one('mro.id')
    parts_id = fields.Many2one('product.product')
    parts_uom = fields.Many2one('product.uom')
    parts_qty = fields.Float('Parts QTY')

    def init(self, cr):
        cr.execute("""create or replace view v_actual_parts_task as
                        select row_number() over()id,
                            ewa_id,parts_id,parts_uom,parts_qty,
                            ewm_id,mro_id ,
                            vtmoa.task_id,mastertask_id from mro_task_parts_line mtpl
                        right join v_task_mro_order_actual vtmoa on vtmoa.task_id = mtpl.task_id""")

