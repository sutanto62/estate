from openerp import models, fields, api, exceptions
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
import time
import datetime
from openerp import tools

class InheritSparepartLog(models.Model):

    _inherit='estate.vehicle.log.sparepart'

    maintenance_id = fields.Integer()

class InheritProduct(models.Model):

    _inherit = 'product.template'

    part_number = fields.Char('Part Number')

class InheritSparepartids(models.Model):

    _inherit = 'mro.order'

    type_service = fields.Selection([('1','Vehicle'),
                                     ('2','Building'),('3','Machine'),('4','Computing'),('5','Tools'),('6','ALL')],readonly=True)
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
                self.create(type)
            return request.id

            # return order_id




class MasterTask(models.Model):

    _name = 'estate.workshop.mastertask'
    _description = 'Master task for maintenance'

    name=fields.Char('Master Task')
    planned_hour = fields.Float('Plan Hour')
    planned_manpower = fields.Float('ManPower')
    owner_id = fields.Integer()
    mastertaskline_ids= fields.One2many('estate.workshop.mastertaskline','mastertask_id')
    type_task = fields.Selection([('1','Preventiv'),('2','Corective')])
    type_preventive = fields.Selection([('1','Periodic'),('2','Schedule Overhoul'),('3','Condition')],defaults=1)
    type_corective = fields.Selection([('1','Repair'),('2','BreakDown')])
    typetask_id = fields.Many2one('estate.master.type.task')

    #onchange
    @api.multi
    @api.onchange('type_task','type_preventive','type_corective','typetask_id')
    def _onchange_typetask_id(self):
        arrType=[]
        if self.type_task == '1':
            if self.type_preventive == '1':
                listtype = self.env['estate.master.type.task'].search([('type_task','=','1'),('type','=','normal')])
                for a in listtype:
                    arrType.append(a.id)
                return {
                    'domain':{
                        'typetask_id':[('id','in',arrType)]
                    }
                }
            elif self.type_preventive == '2':
                listtype = self.env['estate.master.type.task'].search([('type_task','=','2'),('type','=','normal')])
                for a in listtype:
                    arrType.append(a.id)
                return {
                    'domain':{
                        'typetask_id':[('id','in',arrType)]
                    }
                }
            elif self.type_preventive == '3' :
                listtype = self.env['estate.master.type.task'].search([('type_task','=','3'),('type','=','normal')])
                for a in listtype:
                    arrType.append(a.id)
                return {
                    'domain':{
                        'typetask_id':[('id','in',arrType)]
                    }
                }

        elif self.type_task == '2' :
            if self.type_corective == '1' :
                listtype = self.env['estate.master.type.task'].search([('type_task','=','4'),('type','=','normal')])
                for a in listtype:
                    arrType.append(a.id)
                return {
                    'domain':{
                        'typetask_id':[('id','in',arrType)]
                    }
                }
            elif self.type_corective == '2' :
                listtype = self.env['estate.master.type.task'].search([('type_task','=','5'),('type','=','normal')])
                for a in listtype:
                    arrType.append(a.id)
                return {
                    'domain':{
                        'typetask_id':[('id','in',arrType)]
                    }
                }


class MasterTaskLine(models.Model):

    _name = 'estate.workshop.mastertaskline'

    name=fields.Char('Master Task Line')
    task_id=fields.Many2one('mro.task')
    mastertask_id = fields.Integer()

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
    mastersheduletask_ids = fields.One2many('estate.master.workshop.shedule.planline','catalog_id')
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
    catalog_id = fields.Integer()

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
    service_id = fields.Many2one('fleet.vehicle.log.services')
    owner_id = fields.Integer()

class inheritCostWorkshop(models.Model):
    _inherit = 'mro.order'

    cost_ids = fields.One2many('estate.workshop.cost','owner_id')

class CostWorkshop(models.Model):

    _name = 'estate.workshop.cost'

    name= fields.Char()
    component = fields.Char()
    amount = fields.Float()
    owner_id = fields.Integer()

class PlannedTask(models.Model):

    _name = 'estate.workshop.plannedtask'
    _inherits = {'estate.workshop.actualtask':'actualtask_id'}

    actualtask_id = fields.Many2one('estate.workshop.actualtask',required=True,ondelete='cascade')

class ActualTask(models.Model):

    _name = 'estate.workshop.actualtask'

    mastertask_id = fields.Many2one('estate.workshop.mastertask')
    owner_id = fields.Integer()
    planned_hour = fields.Float(readonly=True)
    planned_manpower = fields.Float(readonly=True)

      #onchange
    @api.multi
    @api.onchange('planned_hours','planned_mainpower','mastertask_id')
    def _onchange_planhourn_maintenance(self):
        if self:
            if self.mastertask_id:
                self.planned_hour += self.mastertask_id.planned_hour
                self.planned_manpower += self.mastertask_id.planned_manpower

class InheritPlannedtask(models.Model):

    _inherit = 'mro.order'

    task_ids = fields.One2many('estate.workshop.plannedtask','owner_id')
    actualtask_ids = fields.One2many('estate.workshop.actualtask','owner_id')

