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

# class InheritMroOnchangeOwnerId(models.Model):
#
#     _inherit = 'mro.order'
#
#     @api.multi
#     @api.onchange('owner_id','asset_id'):
#     def _onchange_orner_id(self):
#         if self.asset_id :

class InheritSparepartLog(models.Model):

    _inherit='estate.vehicle.log.sparepart'

    maintenance_id = fields.Integer()

class InheritProduct(models.Model):

    _inherit = 'product.template'

    part_number = fields.Char('Part Number')

class InheritSparepartids(models.Model):

    _inherit = 'mro.order'

    type_service = fields.Selection([('1','Vehicle'),
                                     ('2','Building'),('3','Machine'),('4','Computing'),('5','Tools'),('6','ALL')],
                                    )
    # sparepartlog_ids=fields.One2many('estate.vehicle.log.sparepart','maintenance_id',"Part Log",
    #                                          readonly=True, states={'draft':[('readonly',False)]})

    #onchange
    @api.multi
    @api.onchange('asset_id','type_service')
    def onchange_type_service(self):
        if self.asset_id:
            self.type_service = self.asset_id.type_asset

class InheritTypeAsset(models.Model):

    _inherit =  'mro.request'
    _description = 'Notification workshop for corrective Maintenance'

    type_asset = fields.Selection([('1','Vehicle'),
                                     ('2','Building'),('3','Machine'),('4','Computing'),('5','Tools'),('6','ALL')],readonly=True)

    #onchange
    @api.multi
    @api.onchange('asset_id','type_asset')
    def onchange_type_asset(self):
        if self.asset_id:
            self.type_asset = self.asset_id.type_asset

    @api.multi
    def action_confirm(self):
        """
        Update type_service into approved
        :return: True
        """
        super(InheritTypeAsset, self).action_confirm()

        if self.type_asset:
            print 'terbaca'
            # order = self.pool.get('mro.order')
            order_id = False
            print 'jalankan'
            for request in self.env['mro.order'].search([('id','=',self.id)]):
                print 'aaaaa'
                print request
                type = {
                    'date_planned':self.requested_date,
                    'date_scheduled':self.requested_date,
                    'date_execution':self.requested_date,
                    'origin': self.name,
                    'state': 'draft',
                    'maintenance_type': 'bm',
                    'asset_id': self.asset_id.id,
                    'description': self.cause,
                    'requester_id': self.requester_id.id,
                    'location_id' : self.location_id.id,
                    'cause' : self.cause,
                    'problem_description': self.description,
                    'type_service' : self.type_asset
                }
                self.write(type)


class MasterTask(models.Model):

    _name = 'estate.workshop.mastertask'
    _description = 'Master task for maintenance'

    name=fields.Char('Master Task')
    asset_id = fields.Many2one('asset.asset')
    planned_hour = fields.Float('Plan Hour')
    planned_manpower = fields.Float('ManPower')
    owner_id = fields.Integer()
    mastertaskline_ids= fields.One2many('estate.workshop.mastertaskline','mastertask_id')
    type_task1 = fields.Many2one('estate.master.type.task',domain=[('type','=','view'),('parent_id','=',False)])
    type_subtask = fields.Many2one('estate.master.type.task','sub task')
    type_list_task = fields.Many2one('estate.master.type.task','List task')



    #onchange
    @api.multi
    @api.onchange('type_task1','type_subtask')
    def _onchange_subtask(self):
        arrType=[]
        if self.type_task1:
                listtype = self.env['estate.master.type.task'].search([('parent_id.id','=',self.type_task1.id)])
                for a in listtype:
                    arrType.append(a.id)
                return {
                    'domain':{
                        'type_subtask':[('id','in',arrType)]
                    }
                }
    @api.multi
    @api.onchange('type_subtask','type_list_task')
    def _onchange_list_task(self):
        arrType=[]
        if self.type_subtask:
                listtype = self.env['estate.master.type.task'].search([('parent_id.id','=',self.type_subtask.id)])
                for a in listtype:
                    arrType.append(a.id)
                return {
                    'domain':{
                        'type_list_task':[('id','in',arrType)]
                    }
                }


class MasterTaskLine(models.Model):

    _name = 'estate.workshop.mastertaskline'

    name=fields.Char('Master Task Line')
    task_id=fields.Many2one('mro.task')
    mastertask_id = fields.Many2one('estate.workshop.mastertask')
    key = fields.Integer()
    #onchange
    @api.multi
    @api.onchange('task_id')
    def _onchange_task_id(self):
        arrMastertask = []
        if self:
            self.key = self.mastertask_id.asset_id
            return {
                    'domain' :{
                        'task_id' :[('asset_id.id','=',self.key)]
                    }
            }


class MasterTypeTask(models.Model):

    _name = 'estate.master.type.task'
    _order = 'complete_name'

    name=fields.Char('Name Type')
    complete_name = fields.Char("Complete Name", compute="_complete_name", store=True)
    parent_id = fields.Many2one('estate.master.type.task', "Parent Category", ondelete='restrict')
    parent_left = fields.Integer("Parent Left",	index=True)
    parent_right = fields.Integer("Parent Right", index=True)
    child_ids = fields.One2many('estate.master.type.task', 'parent_id', "Child Type")
    type= fields.Selection([('view', "View"),
                             ('normal', "Normal")], "Type",
                            required=True,
                            help="Select View to create group of activities.")
    type_task= fields.Selection([('1','Periodic'),('2','Schedule Overhoul'),
                            ('3','Condition'),('4','Repair'),('5','BreakDown')])
    description=fields.Text()

    @api.one
    @api.depends('name', 'parent_id')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        if self.parent_id:
            self.complete_name = self.parent_id.complete_name + ' / ' + self.name
        else:
            self.complete_name = self.name

        return True

class MasterSheduleMaintenance(models.Model):

    _name = 'estate.master.shedule'

    name= fields.Char()
    date = fields.Date()
    odometer_min = fields.Float()
    odometer_max = fields.Float()


class MasterCatalog(models.Model):

    _name='estate.part.catalog'
    _order = 'complete_name'

    name=fields.Char('Master Catalog')
    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    parent_id = fields.Many2one('estate.part.catalog', "Parent Category", ondelete='restrict')
    parent_left = fields.Integer("Parent Left",	index=True)
    parent_right = fields.Integer("Parent Right", index=True)
    child_ids = fields.One2many('estate.part.catalog', 'parent_id', "Child Type")
    type= fields.Selection([('view', "View"),
                             ('normal', "Normal")], "Type",
                            required=True,
                            help="Select View to create group of activities.")
    asset_id = fields.Many2one('asset.asset')
    categoryline_ids = fields.One2many('estate.part.catalogline','catalog_id','catalog_line')
    category_id = fields.Many2one('master.category.unit')


    @api.one
    @api.depends('name', 'parent_id')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        if self.parent_id:
            self.complete_name = self.parent_id.complete_name + ' / ' + self.name
        else:
            self.complete_name = self.name

        return True

class MasterCatalogLine(models.Model):

    _name = 'estate.part.catalogline'

    name = fields.Char('Catalog Line')
    product_id = fields.Many2one('product.product')
    part_number = fields.Char('Part Number')
    quantity_part = fields.Float('Quantity Part',)
    product_qty = fields.Float('Product Quantity', required=True),
    qty_available = fields.Float(digits=(2,2))
    product_uom = fields.Many2one('product.uom')
    type = fields.Selection([('normal', 'Normal'), ('phantom', 'Phantom')], 'BoM Line Type', required=True,
                help="Phantom: this product line will not appear in the raw materials of manufacturing orders,"
                     "it will be directly replaced by the raw materials of its own BoM, without triggering"
                     "an extra manufacturing order.")
    catalog_id = fields.Integer()

    @api.multi
    @api.onchange('qty_available','product_id')
    def _onchange_qty_available(self):
        arrQty=[]
        if self:
            if self.product_id:
                qty = self.env['stock.quant'].search([('product_id.id','=',self.product_id.id)])
                for a in qty:
                    arrQty.append(a.qty)
                for a in arrQty:
                    qty = float(a)
                    self.qty_available = qty



class MecanicTimesheets(models.Model):

    _name = 'estate.mecanic.timesheet'
    _inherits = {'estate.timesheet.activity.transport':'timesheet_id'}

    mastertask_id = fields.Many2one('estate.workshop.mastertask')
    timesheet_id = fields.Many2one('estate.timesheet.activity.transport',ondelete='cascade',required=True)
    asset_id = fields.Many2one('asset.asset')
    key = fields.Integer()

    #onchange
    @api.multi
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        arrEmployee=[]
        if self:
            employee = self.env['estate.workshop.employeeline'].search([('mro_id','=',self.owner_id)])
            for a in employee:
                arrEmployee.append(a.employee_id.id)
            return {
                    'domain':{
                        'employee_id':[('id','in',arrEmployee)]
                    }
                }
        return super(MecanicTimesheets, self)._onchange_employee_id()

    @api.multi
    @api.onchange('dc_type')
    def _onchange_dc_type(self):
        if self:
            self.dc_type = 4

    @api.multi
    @api.onchange('mastertask_id')
    def _onchange_mastertask_id(self):
        arrOrder = []
        if self:
            mroorder = self.env['mro.order'].search([('id','=',self.owner_id)])
            for order in mroorder:
                arrOrder.append(order.asset_id.id)
            return {
                'domain':{
                    'mastertask_id':[('asset_id.id','in',arrOrder)]
                }
            }

    @api.multi
    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        arrAsset =[]
        if self:
            asset = self.env['mro.order'].search([('id','=',self.owner_id)])
            for b in asset:
                arrAsset.append(b.asset_id.id)
            return {
                    'domain':{
                        'asset_id':[('id','in',arrAsset)]
                    }
                }

    @api.multi
    @api.onchange('activity_id')
    def _onchange_activity_id(self):
        arrActivity=[]
        if self:
            # todo Change activity
            # mroorder = self.env['mro.order'].search([('id','=',self.owner_id)]).type_service
            # print mroorder
            # if mroorder == 1 :
            activity = self.env['estate.activity'].search([('activity_type','=','general'),('parent_id','!=',False)])
            for a in activity:
                arrActivity.append(a.id)
            return {
                    'domain':{
                        'activity_id':[('id','in',arrActivity)]
                    }
                }
        return super(MecanicTimesheets, self)._onchange_activity_id()

    @api.multi
    @api.onchange('vehicle_id','asset_id')
    def _onchange_vehciel_id(self):
        if self:
            self.vehicle_id = self.asset_id.fleet_id

class WorkshopCode(models.Model):

    _name = 'estate.workshop.causepriority.code'

    name=fields.Char('Code Name')
    type=fields.Selection([('1','Failure'),('2','Priority'),('3','Reconciliation')])


class InheritTimesheetMro(models.Model):

    _inherit = 'mro.order'

    mecanictimesheet_ids = fields.One2many('estate.mecanic.timesheet','owner_id')
    employeeline_ids = fields.One2many('estate.workshop.employeeline','mro_id')
    serviceexternal_ids = fields.One2many('estate.workshop.external.service','owner_id')

class EmployeeLine(models.Model):

    _name = 'estate.workshop.employeeline'

    employee_id = fields.Many2one('hr.employee')
    mro_id = fields.Integer()

class InheritMaintenanceRequest(models.Model):

    _inherit = 'mro.request'

    code_id = fields.Many2one('estate.workshop.causepriority.code','Cause Failure',domain=[('type', '=', '1')])

    #onchange
    @api.multi
    @api.onchange('code_id','cause')
    def _onchange_cause(self):
        if self.code_id:
            self.cause = self.code_id.name

class InheritMaintenanceOrder(models.Model):

    _inherit = 'mro.order'

    code_id = fields.Many2one('estate.workshop.causepriority.code','Priority',domain=[('type', '=', '2')])
    reconcil_id = fields.Many2one('estate.workshop.causepriority.code',domain=[('type', '=', '3')])

class MasterWorkshopShedulePlan(models.Model):

    _name = 'estate.master.workshop.shedule.plan'
    _order = 'complete_name'


    name = fields.Char('Shedule Name')
    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    parent_id = fields.Many2one('estate.master.workshop.shedule.plan', "Parent Category", ondelete='restrict')
    parent_left = fields.Integer("Parent Left",	index=True)
    parent_right = fields.Integer("Parent Right", index=True)
    child_ids = fields.One2many('estate.master.workshop.shedule.plan', 'parent_id', "Child Type")
    type= fields.Selection([('view', "View"),
                             ('normal', "Normal")], "Type",
                            required=True,
                            help="Select View to create group of activities.")
    odometer = fields.Float('KM Plan')
    asset_id = fields.Many2one('asset.asset')
    mastersheduletask_ids = fields.One2many('estate.master.workshop.shedule.planline','owner_id')
    type_service=fields.Selection([('1','Weekly'),('2','Monthly'),('3','Yearly')])
    category_id = fields.Many2one('master.category.unit')

    @api.one
    @api.depends('name', 'parent_id')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        if self.parent_id:
            self.complete_name = self.parent_id.complete_name + ' / ' + self.name
        else:
            self.complete_name = self.name

        return True

class MasterWorkshopShedulePlanLine(models.Model):

    _name = 'estate.master.workshop.shedule.planline'

    name = fields.Char('master workshop shedule Line')
    mastertask_id = fields.Many2one('estate.workshop.mastertask')
    owner_id = fields.Integer()

class MasterMappingAssetActivity(models.Model):

    _name = 'estate.workshop.mastermappingasset'

    name = fields.Char('Master Mapping Asset')
    mastergrouptask_id = fields.Many2one('estate.workshop.mastertask')
    mastermappingline_ids= fields.One2many('estate.workshop.mastermappingassetline','mastermapping_id')

    # Constraint to Asset Not more than 1
    @api.one
    @api.constrains('mastermappingline_ids')
    def _constrains_asset(self):
        if self.mastermappingline_ids:
            temp={}
            for asset in self.mastermappingline_ids:
                asset_value_name = asset. asset_id
                if asset_value_name in temp.values():
                    error_msg = "Asset Choose \"%s\" is set more than once " % asset_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[asset.id] = asset_value_name
            return temp



class MasterMappingAssetLine(models.Model):

    _name = 'estate.workshop.mastermappingassetline'

    asset_id = fields.Many2one('asset.asset')
    mastermapping_id = fields.Integer()

class ActualEquipment(models.Model):

    _name = 'estate.workshop.actualequipment'

    name = fields.Char('Actual Equipment')
    asset_id = fields.Many2one('asset.asset',domain=[('type_asset', '=', '5')])
    mro_id = fields.Integer()
    ownership = fields.Selection([('1','Internal'),('2','External')])
    uom_id = fields.Many2one('product.uom',store=True)
    unit = fields.Float(digits=(2,2))
    description = fields.Text()

class PlannedEquipment(models.Model):

    _name = 'estate.workshop.plannedequipment'
    _inherits = {'estate.workshop.actualequipment':'actualtools_id'}

    actualtools_id = fields.Many2one('estate.workshop.actualequipment',ondelete='cascade',required=True)

    @api.multi
    @api.onchange('uom_id','asset_id')
    def _onchange_uom_id(self):
        """ Finds UoM and UoS of changed product.
        @param product_id: Changed id of product.
        @return: Dictionary of values.
        """
        if self.asset_id:
            w = self.env['product.product'].search([('id','=',self.asset_id.product_id.id)])
            self.uom_id = w.uom_id.id

class InheritEquipment(models.Model):

    _inherit = 'mro.order'

    actualtools_ids= fields.One2many('estate.workshop.actualequipment','mro_id')
    plannedtools_ids = fields.One2many('estate.workshop.plannedequipment','mro_id')

class ExternalOrder(models.Model):

    _inherits = {'fleet.vehicle.log.services':'service_id'}
    _name = 'estate.workshop.external.service'

    def on_change_vehicle(self, cr, uid, ids, vehicle_id, context=None):
        if not vehicle_id:
            return {}
        vehicle = self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_id, context=context)
        odometer_unit = vehicle.odometer_unit
        driver = vehicle.driver_id.id
        return {
            'value': {
                'odometer_unit': odometer_unit,
                'purchaser_id': driver,
            }
        }

    def _get_default_service_type(self, cr, uid, context):
        try:
            model, model_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'fleet', 'type_service_service_8')
        except ValueError:
            model_id = False
        return model_id

    name = fields.Char()
    service_id = fields.Many2one('fleet.vehicle.log.services',required=True,ondelete='cascade')
    employee_id = fields.Many2one('hr.employee','Requester')
    owner_id = fields.Integer()

class inheritCostWorkshop(models.Model):
    _inherit = 'mro.order'

    cost_ids = fields.One2many('v.summary.cost.workshop.detail','mo_id')


class PlannedTask(models.Model):

    _name = 'estate.workshop.plannedtask'
    _inherits = {'estate.workshop.actualtask':'actualtask_id'}

    actualtask_id = fields.Many2one('estate.workshop.actualtask',required=True,ondelete='cascade')

    #onchange
    @api.multi
    @api.onchange('planned_hour','planned_manpower','mastertask_id')
    def _onchange_planhourn_maintenance(self):
        if self:
            if self.mastertask_id:
                self.planned_hour += self.mastertask_id.planned_hour
                self.planned_manpower += self.mastertask_id.planned_manpower

    @api.multi
    @api.onchange('mastertask_id','owner_id')
    def _onchange_mastertask_id(self):
        arrOrder = []
        if self:
            order = self.env['mro.order'].search([('id','=',self.owner_id)])
            for order in order:
                arrOrder.append(order.asset_id.id)
            return {
                'domain':{
                    'mastertask_id' : [('asset_id','in',arrOrder)]
                }
            }

    # @api.multi
    # @api.onchange('mastertask_id','owner_id','asset_id')
    # def _onchange_owner_id(self):
    #     self.owner_id = self.asset_id.id

    # @api.multi
    # @api.onchange('mastertask_id','owner_id')
    # def _onchange_mastertask_id(self):



class ActualTask(models.Model):

    _name = 'estate.workshop.actualtask'

    mastertask_id = fields.Many2one('estate.workshop.mastertask')
    asset_id = fields.Many2one('asset.asset')
    owner_id = fields.Integer()
    planned_hour = fields.Float(readonly=True)
    planned_manpower = fields.Float(readonly=True)





class InheritPlannedtask(models.Model):

    _inherit = 'mro.order'

    task_ids = fields.One2many('estate.workshop.plannedtask','owner_id')
    actualtask_ids = fields.One2many('estate.workshop.actualtask','owner_id')


    # todo create new line in sparepart
    @api.multi
    @api.onchange('plannedpart_ids','task_ids')
    def _onchange_part_line(self):
        if self.task_ids:
            listmastertask = self.env['estate.workshop.plannedtask'].search([('owner_id','=',self.id)]).mastertask_id
            for listmastertask in listmastertask:
                mastertask = self.env['estate.workshop.mastertask'].search([('id','=',listmastertask[0].id)])
                taskline = self.env['estate.workshop.mastertaskline'].search([('mastertask_id','=',mastertask[0].id)]).task_id
                task = self.env['mro.task'].search([('id','=',taskline[0].id)])
                taskpartline = self.env['mro.task.parts.line'].search([('task_id.id','=',task[0].id)])
                print 'test part'
                print taskpartline
                #clear old parts
                # new_parts_lines = [[2,line[1],line[2]] for line in self.plannedpart_ids if line[0]]
                #copy parts from task
                for line in taskpartline:
                    self.plannedpart_ids.append([0,0,{
                        'name': line.name,
                        'product_id': line.parts_id.id,
                        'qty_product': line.parts_qty,
                        'uom_id': line.parts_uom.id,
                        }])
                    print'test new line'
                    print self.plannedpart_ids
                return {'value': {
                    'plannedpart_ids': self.plannedpart_ids,
                }}

class InheritHrContract(models.Model):

    _inherit = 'hr.contract'

    weekly_wage = fields.Float(readonly=True)
    daily_wage = fields.Float(readonly=True)
    hourly_wage = fields.Float(readonly=True)
    day = fields.Float()
    hour = fields.Float()

    #Onchange
    @api.multi
    @api.onchange('wage','weekly_wage','daily_wage','hourly_wage','day','hour')
    def _onchange_wage(self):
        if self.wage and self.hour and self.day:
            self.weekly_wage = self.wage/int(4)
            self.daily_wage = self.weekly_wage/float(self.day)
            self.hourly_wage = self.daily_wage/float(self.hour)

class PlannedSparepart(models.Model):
    _inherits = {'estate.workshop.actual.sparepart':'actualpart_id'}
    _name = 'estate.workshop.planned.sparepart'

    actualpart_id = fields.Many2one('estate.workshop.actual.sparepart',required=True,ondelete='cascade')

    @api.multi
    @api.onchange('qty_available','product_id')
    def _onchange_get_qty_available(self):
        arrQty=[]
        if self:
            if self.product_id:
                qty = self.env['stock.quant'].search([('product_id.id','=',self.product_id.id)])
                for a in qty:
                    arrQty.append(a.qty)
                for a in arrQty:
                    qty = float(a)
                    self.qty_available = qty

    # @api.multi
    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     arrProduct =[]
    #     if self:
    #         listmastertask = self.env['estate.workshop.plannedtask'].search([('owner_id','=',self.owner_id)]).mastertask_id
    #         for listmastertask in listmastertask:
    #             mastertask = self.env['estate.workshop.mastertask'].search([('id','=',listmastertask[0].id)])
    #             taskline = self.env['estate.workshop.mastertaskline'].search([('mastertask_id','=',mastertask[0].id)]).task_id
    #             taskpartline = self.env['mro.task.parts.line'].search([('task_id.id','=',taskline[0].id)]).parts_id
    #             arrProduct.append(taskpartline.id)
    #         return {
    #             'domain':{
    #                 'product_id' : [('id','in',arrProduct)]
    #             }
    #         }

    @api.multi
    @api.onchange('uom_id','product_id')
    def _onchange_uom_id(self):
        """ Finds UoM and UoS of changed product.
        @param product_id: Changed id of product.
        @return: Dictionary of values.
        """
        if self.product_id:
            w = self.env['product.product'].search([('id','=',self.product_id.id)])
            self.uom_id = w.uom_id.id


    @api.multi
    @api.constrains('qty_available' , 'qty_product')
    def _contraints_qty_product(self):
        if self:
            if self.qty_product > self.qty_available:
                error_msg = "Qty Product not more than \"%s\" in Qty Available, Create PP " % self.qty_available
                raise exceptions.ValidationError(error_msg)
        return True

class ActualSparepart(models.Model):

    _name = 'estate.workshop.actual.sparepart'

    name = fields.Char()
    product_id = fields.Many2one('product.product',)
    qty_product = fields.Float()
    uom_id = fields.Many2one('product.uom')
    qty_available = fields.Float(readonly=True,store=True)
    owner_id = fields.Integer()



class InheritMroSparepart(models.Model):

    _inherit = 'mro.order'

    actualpart_ids = fields.One2many('estate.workshop.actual.sparepart','owner_id')
    plannedpart_ids = fields.One2many('estate.workshop.planned.sparepart','owner_id')


class ProcurPart(models.Model):

    _inherits = {'procurement.order':'procur_id'}
    _name = 'estate.workshop.procurement'
    _inherit = ['mail.thread']

    def _default_session(self):
        return self.env['mro.order'].browse(self._context.get('active_id'))

    procur_id = fields.Many2one('procurement.order',required=True,ondelete='cascade')
    order_id = fields.Many2one('mro.order',default=_default_session)


    def do_view_procurements(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing procurement orders
        of same procurement group of given ids.
        '''
        act_obj = self.pool.get('ir.actions.act_window')
        action_id = self.pool.get('ir.model.data').xmlid_to_res_id(cr, uid, 'procurement.do_view_procurements', raise_if_not_found=True)
        result = act_obj.read(cr, uid, [action_id], context=context)[0]
        group_ids = set([proc.group_id.id for proc in self.browse(cr, uid, ids, context=context) if proc.group_id])
        result['domain'] = "[('group_id','in',[" + ','.join(map(str, list(group_ids))) + "])]"
        return result

    @api.multi
    @api.onchange('product_uom','product_uos','product_id')
    def onchange_product_id(self):
        """ Finds UoM and UoS of changed product.
        @param product_id: Changed id of product.
        @return: Dictionary of values.
        """
        if self.product_id:
            w = self.env['product.product'].search([('id','=',self.product_id.id)])
            self.product_uom = w.uom_id.id
            self.product_uos =  w.uos_id and w.uos_id.id or w.uom_id.id

    @api.multi
    @api.onchange('order_id','product_id')
    def _onchange_product_id(self):
        arrProduct = []
        if self.order_id:
            listproduct = self.env['estate.workshop.planned.sparepart'].search([('owner_id','=',self.order_id.id)])
            for product in listproduct:
                arrProduct.append(product.product_id.id)
            return {
                 'domain':{
                        'product_id':[('id','in',arrProduct)]
                    }
            }

    @api.multi
    @api.onchange('origin','order_id')
    def _onchange_origin(self):
        if self.order_id:
            self.origin = self.order_id.name

    def get_cancel_ids(self, cr, uid, ids, context=None):
        return [proc.id for proc in self.browse(cr, uid, ids, context=context) if proc.state != 'done']

    def cancel(self, cr, uid, ids, context=None):
        #cancel only the procurements that aren't done already
        to_cancel_ids = self.get_cancel_ids(cr, uid, ids, context=context)
        if to_cancel_ids:
            return self.write(cr, uid, to_cancel_ids, {'state': 'cancel'}, context=context)

    def reset_to_confirmed(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'confirmed'}, context=context)

    def run(self, cr, uid, ids, autocommit=False, context=None):
        for procurement_id in ids:
            #we intentionnaly do the browse under the for loop to avoid caching all ids which would be resource greedy
            #and useless as we'll make a refresh later that will invalidate all the cache (and thus the next iteration
            #will fetch all the ids again)
            procurement = self.browse(cr, uid, procurement_id, context=context)
            if procurement.state not in ("running", "done"):
                try:
                    if self._assign(cr, uid, procurement, context=context):
                        res = self._run(cr, uid, procurement, context=context or {})
                        if res:
                            self.write(cr, uid, [procurement.id], {'state': 'running'}, context=context)
                        else:
                            self.write(cr, uid, [procurement.id], {'state': 'exception'}, context=context)
                    else:
                        self.message_post(cr, uid, [procurement.id], body='No rule matching this procurement', context=context)
                        self.write(cr, uid, [procurement.id], {'state': 'exception'}, context=context)
                    if autocommit:
                        cr.commit()
                except OperationalError:
                    if autocommit:
                        cr.rollback()
                        continue
                    else:
                        raise
        return True

    def check(self, cr, uid, ids, autocommit=False, context=None):
        done_ids = []
        for procurement in self.browse(cr, uid, ids, context=context):
            try:
                result = self._check(cr, uid, procurement, context=context)
                if result:
                    done_ids.append(procurement.id)
                if autocommit:
                    cr.commit()
            except OperationalError:
                if autocommit:
                    cr.rollback()
                    continue
                else:
                    raise
        if done_ids:
            self.write(cr, uid, done_ids, {'state': 'done'}, context=context)
        return done_ids

    #
    # Method to overwrite in different procurement modules
    #
    def _find_suitable_rule(self, cr, uid, procurement, context=None):
        '''This method returns a procurement.rule that depicts what to do with the given procurement
        in order to complete its needs. It returns False if no suiting rule is found.
            :param procurement: browse record
            :rtype: int or False
        '''
        return False

    def _assign(self, cr, uid, procurement, context=None):
        '''This method check what to do with the given procurement in order to complete its needs.
        It returns False if no solution is found, otherwise it stores the matching rule (if any) and
        returns True.
            :param procurement: browse record
            :rtype: boolean
        '''
        #if the procurement already has a rule assigned, we keep it (it has a higher priority as it may have been chosen manually)
        if procurement.rule_id:
            return True
        elif procurement.product_id.type != 'service':
            rule_id = self._find_suitable_rule(cr, uid, procurement, context=context)
            if rule_id:
                self.write(cr, uid, [procurement.id], {'rule_id': rule_id}, context=context)
                return True
        return False

    def _run(self, cr, uid, procurement, context=None):
        '''This method implements the resolution of the given procurement
            :param procurement: browse record
            :returns: True if the resolution of the procurement was a success, False otherwise to set it in exception
        '''
        return True

    def _check(self, cr, uid, procurement, context=None):
        '''Returns True if the given procurement is fulfilled, False otherwise
            :param procurement: browse record
            :rtype: boolean
        '''
        return False

    #
    # Scheduler
    #
    def run_scheduler(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        '''
        Call the scheduler to check the procurement order. This is intented to be done for all existing companies at
        the same time, so we're running all the methods as SUPERUSER to avoid intercompany and access rights issues.

        @param self: The object pointer
        @param cr: The current row, from the database cursor,
        @param uid: The current user ID for security checks
        @param ids: List of selected IDs
        @param use_new_cursor: if set, use a dedicated cursor and auto-commit after processing each procurement.
            This is appropriate for batch jobs only.
        @param context: A standard dictionary for contextual values
        @return:  Dictionary of values
        '''
        if context is None:
            context = {}
        try:
            if use_new_cursor:
                cr = openerp.registry(cr.dbname).cursor()

            # Run confirmed procurements
            dom = [('state', '=', 'confirmed')]
            if company_id:
                dom += [('company_id', '=', company_id)]
            prev_ids = []
            while True:
                ids = self.search(cr, SUPERUSER_ID, dom, context=context)
                if not ids or prev_ids == ids:
                    break
                else:
                    prev_ids = ids
                self.run(cr, SUPERUSER_ID, ids, autocommit=use_new_cursor, context=context)
                if use_new_cursor:
                    cr.commit()

            # Check if running procurements are done
            offset = 0
            dom = [('state', '=', 'running')]
            if company_id:
                dom += [('company_id', '=', company_id)]
            prev_ids = []
            while True:
                ids = self.search(cr, SUPERUSER_ID, dom, offset=offset, context=context)
                if not ids or prev_ids == ids:
                    break
                else:
                    prev_ids = ids
                self.check(cr, SUPERUSER_ID, ids, autocommit=use_new_cursor, context=context)
                if use_new_cursor:
                    cr.commit()

        finally:
            if use_new_cursor:
                try:
                    cr.close()
                except Exception:
                    pass

        return {}
