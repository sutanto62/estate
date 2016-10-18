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


class InheritSparepartLog(models.Model):

    _inherit='estate.vehicle.log.sparepart'

    maintenance_id = fields.Integer('Maintenance ID')

class InheritProduct(models.Model):

    _inherit = 'product.template'

    part_number = fields.Char('Part Number')

class MasterTask(models.Model):

    _name = 'estate.workshop.mastertask'
    _description = 'Master task for maintenance'

    name=fields.Char('Master Task')
    asset_id = fields.Many2one('asset.asset','Asset')
    planned_hour = fields.Float('Plan Hour')
    planned_manpower = fields.Float('Plan ManPower')
    owner_id = fields.Integer()
    mastertaskline_ids= fields.One2many('estate.workshop.mastertaskline','mastertask_id','Line Master Task')
    type_task1 = fields.Many2one('estate.master.type.task','Task',domain=[('type','=','view'),('parent_id','=',False)])
    category_unit_id = fields.Many2one('master.category.unit','Category')
    type_subtask = fields.Many2one('estate.master.type.task','Sub Task')
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
    @api.onchange('category_unit_id','asset_id')
    def _onchange_category_unit_id(self):

        for record in self:
            if record.asset_id:
                record.category_unit_id = record.asset_id.fleet_id.category_unit_id.id

    @api.multi
    @api.onchange('category_unit_id','asset_id')
    def _onchange_asset_id(self):
        arrAsset = []
        for record in self:
            if record.category_unit_id:
                temp = record.env['fleet.vehicle'].search([('category_unit_id','=',record.category_unit_id.id)])
                for asset in temp:
                    arrAsset.append(asset.id)
                return {
                'domain':{
                    'asset_id' : [('fleet_id','in',arrAsset)]
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
    _description = 'Master Task Line'

    name=fields.Char('Master Task Line')
    task_id=fields.Many2one('mro.task','Task')
    mastertask_id = fields.Many2one('estate.workshop.mastertask')
    key1 = fields.Integer('Key')
    key2 = fields.Integer('Key')

    #onchange
    @api.multi
    @api.onchange('task_id')
    def _onchange_task_id(self):
        arrMastertask = []
        self.key1 = self.mastertask_id.category_unit_id
        self.key2 = self.mastertask_id.asset_id.fleet_id.category_unit_id.id
        if self:
            if self.mastertask_id.category_unit_id:
                return {
                        'domain' :{
                            'task_id' :[('category_unit_id.id','=',self.key1)]
                        }
                }
            if self.mastertask_id.asset_id.fleet_id.category_unit_id.id:
                return {
                        'domain' :{
                            'task_id' :[('category_unit_id.id','=',self.key2)]
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

    name= fields.Char('Master Schedule')
    date = fields.Date('Date')
    odometer_min = fields.Float('Odoometer Minimum')
    odometer_max = fields.Float('Odometer Maximum')


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
    asset_id = fields.Many2one('asset.asset','Asset')
    categoryline_ids = fields.One2many('estate.part.catalogline','catalog_id','Catalog line')
    category_id = fields.Many2one('master.category.unit','Category Unit')


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
    product_qty = fields.Float('Product Quantity', required=True)
    qty_available = fields.Float(digits=(2,2),compute='_onchange_qty_available')
    product_uom = fields.Many2one('product.uom')
    type = fields.Selection([('normal', 'Normal'), ('phantom', 'Phantom')], 'BoM Line Type', required=True,
                help="Phantom: this product line will not appear in the raw materials of manufacturing orders,"
                     "it will be directly replaced by the raw materials of its own BoM, without triggering"
                     "an extra manufacturing order.")
    catalog_id = fields.Integer()

    @api.multi
    @api.depends('qty_available','product_id')
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

    mastertask_id = fields.Many2one('estate.workshop.mastertask','Master Task')
    timesheet_id = fields.Many2one('estate.timesheet.activity.transport',ondelete='cascade',required=True)
    asset_id = fields.Many2one('asset.asset')
    task_id = fields.Many2one('mro.task')
    contract_key = fields.Boolean('Contract Active')
    total_time = fields.Float(digits=(2,2),compute='_compute_total_time')
    key = fields.Integer()

    #onchange
    @api.multi
    @api.onchange('mastertask_id','task_id')
    def _onchange_task_id(self):
        arrTask=[]
        if self.mastertask_id:
            mastertask = self.env['estate.workshop.mastertaskline'].search([('mastertask_id.id','=',self.mastertask_id.id)])
            for task in mastertask :
                arrTask.append(task.task_id.id)
            return {
                    'domain':{
                        'task_id':[('id','in',arrTask)]
                    }
                }

    @api.multi
    def unlink(self):
        self.timesheet_id.unlink()
        return super(MecanicTimesheets, self).unlink()

    @api.multi
    @api.onchange('contract_key','employee_id')
    def _onchange_contract_key(self):
        if self:
            for item in self:
                if item.employee_id:
                    employee = item.env['hr.employee'].search([('id','=',item.employee_id.id)])
                    contract = item.env['hr.contract'].search([('employee_id.id','=',employee[0].id)])
                    for employeecontract in contract:
                        if  employeecontract.date_end != False and employeecontract.date_end <= item.date_activity_transport:
                            self.contract_key = False
                        else :
                            self.contract_key = True


    @api.multi
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        arrEmployee=[]
        #onchange Employee ID same ase employee line
        if self:
            employee = self.env['estate.workshop.employeeline.actual'].search([('mro_id','=',self.owner_id)])
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
            mroorder = self.env['estate.workshop.actualtask'].search([('mro_id','=',self.owner_id)])
            for order in mroorder:
                arrOrder.append(order.mastertask_id.id)
            return {
                'domain':{
                    'mastertask_id':[('id','in',arrOrder)]
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
    def _onchange_vehicle_id(self):
        if self:
            self.vehicle_id = self.asset_id.fleet_id

    @api.multi
    @api.depends('start_time','end_time','total_time')
    def _compute_total_time(self):
        self.ensure_one()
        #to compute total_time
        if self:
            if self.start_time and self.end_time:
                calculate_endtime = round(self.end_time%1*0.6,2)+(self.end_time-self.end_time%1)
                calculate_starttime = round(self.start_time%1*0.6,2)+(self.start_time-self.start_time%1)
                self.total_time =calculate_endtime-calculate_starttime
                if self.total_time < 0 :
                    self.total_time = 0
        return True

class WorkshopCode(models.Model):

    _name = 'estate.workshop.causepriority.code'

    name=fields.Char('Code Name')
    type=fields.Selection([('1','Failure'),('2','Priority'),('3','Reconciliation')])

class EmployeeLine(models.Model):

    _name = 'estate.workshop.employeeline'

    employee_id = fields.Many2one('hr.employee',
                                  domain=[('contract_type','!=','Null'),
                                          ('contract_period','!=','Null'),
                                          ('job_id.name','in',['Helper Mekanik','helper mekanik',
                                                               'helper Mekanik','Helper mekanik','Mekanik','mekanik',
                                                               'Mechanic','mechanic',
                                                               'Sopir','sopir','Driver','driver'])])
    mro_id = fields.Integer('MRO')

class EmployeeLineActual(models.Model):

    _name = 'estate.workshop.employeeline.actual'

    employee_id = fields.Many2one('hr.employee',
                                  domain=[('contract_type','!=','Null'),
                                          ('contract_period','!=','Null'),('job_id.name','=','Mekanik')])
    mro_id = fields.Integer('MRO')

class MasterWorkshopShedulePlan(models.Model):

    _name = 'estate.master.workshop.shedule.plan'
    _order = 'complete_name'
    _description = 'Workshop Schedule Planning'

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

    # @api.multi
    # @api.onchange('asset_id','category_id')
    # def _onchange_category_id(self):
    #     arrUnit=[]
    #     if self.asset_id:
    #         if self.env['asset.asset'].search([('id','=',self.asset_id.id)]).fleet_id:
    #             asset = self.env['asset.asset'].search([('id','=',self.asset_id.id)]).fleet_id
    #             fleet = self.env['fleet.vehicle'].search([('id','=',asset[0].id)]).category_unit_id
    #             categunit = self.env['master.category.unit'].search([('id','=',fleet[0].id)])
    #             for unit in categunit:
    #                 arrUnit.append(unit.id)
    #                 return {
    #                     'domain':{
    #                      'category_id' : [('id','in',arrUnit)]
    #                     }
    #                 }
    #         elif self.asset_id != self.env['asset.asset'].search([('id','=',self.asset_id.id)]).fleet_id:
    #             categunit = self.env['master.category.unit'].search([('type','=','2')])
    #             for unit in categunit:
    #                 arrUnit.append(unit.id)
    #                 return {
    #                     'domain':{
    #                      'category_id' : [('id','in',arrUnit)]
    #                     }
    #                 }
    #         else:
    #             return {
    #                 'domain':{
    #                      'category_id' : [('id','=',False)]
    #                     }
    #             }

class MasterWorkshopShedulePlanLine(models.Model):

    _name = 'estate.master.workshop.shedule.planline'
    _description = 'Workshop Schedulling Planning Line'

    name = fields.Char('master workshop shedule Line')
    mastertask_id = fields.Many2one('estate.workshop.mastertask','Master Task')
    owner_id = fields.Integer('Owner')

class MasterMappingAssetActivity(models.Model):

    _name = 'estate.workshop.mastermappingasset'
    _description = 'Workshop Master Mapping Asset'

    name = fields.Char('Master Mapping Asset')
    mastergrouptask_id = fields.Many2one('estate.workshop.mastertask','Group Task')
    mastermappingline_ids= fields.One2many('estate.workshop.mastermappingassetline','mastermapping_id','Master Mapping Asset Line')

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
    _description = 'Master Mapping Asset Line'

    asset_id = fields.Many2one('asset.asset','Asset')
    mastermapping_id = fields.Integer('Master Mapping ID')

class ExternalOrder(models.Model):

    _inherits = {'fleet.vehicle.log.services':'service_id'}
    _name = 'estate.workshop.external.service'
    _description = 'External Order'

    def on_change_vehicle(self, cr, uid, ids, vehicle_id, context=None):
        if not vehicle_id:
            return {}
        vehicle = self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_id, context=context)
        cr.execute('select max(value) as value_odometer from fleet_vehicle_odometer where vehicle_id = %d' %(vehicle.id))
        odometer = cr.fetchone()[0]
        odometer_unit = vehicle.odometer_unit
        driver = vehicle.driver_id.id
        return {
            'value': {
                'odometer_unit': odometer_unit,
                'odometer' : odometer,
                'purchaser_id': driver,
            }
        }

    def _get_default_service_type(self, cr, uid, context):
        try:
            model, model_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'fleet', 'type_service_service_8')
        except ValueError:
            model_id = False
        return model_id

    name = fields.Char('External Order')
    service_id = fields.Many2one('fleet.vehicle.log.services',required=True,ondelete='cascade')
    asset_id = fields.Many2one('asset.asset','Asset')
    employee_id = fields.Many2one('hr.employee','Requester')
    cost_ids = fields.One2many('fleet.vehicle.cost','parent_id')
    owner_id = fields.Integer()

    @api.multi
    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        arrAsset = []
        if self:
            mro = self.env['mro.order'].search([('id','=',self.owner_id)])
            for asset in mro:
               arrAsset.append(asset.asset_id.id)
            return {
                'domain' : {
                    'asset_id' : [('id','=',arrAsset)]
                }
            }

    @api.multi
    @api.onchange('vehicle_id','asset_id')
    def _onchange_vehicle_id(self):
        if self:
            self.vehicle_id = self.asset_id.fleet_id.id

    @api.multi
    @api.onchange('employee_id','asset_id')
    def _onchange_requester(self):
        if self.asset_id:
            self.employee_id = self.env['mro.order'].search([('id','=',self.owner_id)]).requester_id

    @api.multi
    @api.onchange('inv_ref','asset_id')
    def _onchange_invoice_reverence(self):
        if self.asset_id:
            self.inv_ref = self.env['mro.order'].search([('id','=',self.owner_id)]).name

    # constraint
    @api.multi
    @api.constrains('cost_ids')
    def _constraint_amount(self):
        self.ensure_one()
        if self.cost_ids:
            temp={}
            for costtype in self.cost_ids:
                costtype_value_name = costtype.cost_subtype_id.name
                if costtype_value_name in temp.values():
                    error_msg = "Service \"%s\" is set more than once " % costtype_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[costtype.id] = costtype_value_name
            return temp


class PlannedSparepart(models.Model):

    _name = 'estate.workshop.planned.sparepart'
    _description = 'Planning Sparepart'

    name = fields.Char('Planned Sparepart')
    qty_available = fields.Float('Quantity Available',readonly=False,store=True)
    product_id = fields.Many2one('product.product','Product')
    qty_product = fields.Float('Quantity Product')
    uom_id = fields.Many2one('product.uom','UOM')
    owner_id = fields.Integer('Owner')

    @api.multi
    @api.onchange('qty_available','product_id')
    def _onchange_get_qty_available(self):
        arrQty=[]
        if self.product_id:
            qty = self.env['stock.quant'].search([('product_id.id','=',self.product_id.id)])
            for a in qty:
                arrQty.append(a.qty)
            for a in arrQty:
                qty = float(a)
                self.qty_available = qty


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
    _description = 'Actual Sparepart'

    name = fields.Char('Actual Sparepart')
    product_id = fields.Many2one('product.product','Product')
    qty_product = fields.Float('Quantity Product')
    uom_id = fields.Many2one('product.uom','UOM')
    qty_available = fields.Float('Quantity Available',readonly=False,store=True)
    owner_id = fields.Integer('Owner')

    @api.multi
    @api.onchange('qty_available','product_id')
    def _onchange_get_qty_available(self):
        arrQty=[]
        if self.product_id:
            qty = self.env['stock.quant'].search([('product_id.id','=',self.product_id.id)])
            for a in qty:
                arrQty.append(a.qty)
            for a in arrQty:
                qty = float(a)
                self.qty_available = qty


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

class ProcurPart(models.Model):

    _inherits = {'procurement.order':'procur_id'}
    _name = 'estate.workshop.procurement'
    _inherit = ['mail.thread']
    _description = 'Procurment Order'

    def _default_session(self):
        return self.env['mro.order'].browse(self._context.get('active_id'))

    procur_id = fields.Many2one('procurement.order',required=True,ondelete='cascade')
    order_id = fields.Many2one('mro.order',default=_default_session)
    product_uos_qty = fields.Float('Uos Quantity')
    product_uos = fields.Many2one('product.uom','Product UoS')


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
            # self.product_uos =  w.uos_id and w.uos_id.id or w.uom_id.id

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
