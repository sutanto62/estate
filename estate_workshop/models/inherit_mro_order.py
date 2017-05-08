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


class InheritMroOrder(models.Model):

    _inherit = 'mro.order'

    mecanictimesheet_ids = fields.One2many('estate.mecanic.timesheet','owner_id')
    employeeline_ids = fields.One2many('estate.workshop.employeeline','mro_id')
    employeelineactual_ids = fields.One2many('estate.workshop.employeeline.actual','mro_id')
    serviceexternal_ids = fields.One2many('estate.workshop.external.service','owner_id')
    code_id = fields.Many2one('estate.workshop.causepriority.code','Priority',domain=[('type', '=', '2')])
    reconcil_id = fields.Many2one('estate.workshop.causepriority.code',domain=[('type', '=', '3')],
                                  states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
    actualtools_ids= fields.One2many('estate.workshop.actualequipment','mro_id')
    plannedtools_ids = fields.One2many('estate.workshop.plannedequipment','mro_id')
    cost_ids = fields.One2many('v.summary.cost.workshop.detail','mo_id')
    plannedtask_ids = fields.One2many('estate.workshop.plannedtask','mro_id')
    actualtask_ids = fields.One2many('estate.workshop.actualtask','mro_id')
    actualpart_ids = fields.One2many('estate.workshop.actual.sparepart','owner_id')
    plannedpart_ids = fields.One2many('estate.workshop.planned.sparepart','owner_id')
    typetask_id = fields.Many2one('estate.master.type.task','Type Task',domain=[('parent_id','=',False)])
    type_service = fields.Selection([('1','Vehicle'),
                                     ('2','Building'),('3','Machine'),('4','Computing'),('5','Tools'),('6','ALL')],
                                    )
    image = fields.Binary('image',help="Select image here")
    category_unit_id = fields.Integer('Category')
    category_name = fields.Char('Category',compute='_onchange_category_unit_name')

    # Group code constraint
    @api.multi
    @api.constrains('plannedtask_ids')
    def _constrains_plannedmastertask_id(self):
        self.ensure_one()
        if self.plannedtask_ids:
            temp={}
            for task in self.plannedtask_ids:
                task_value_name = task.mastertask_id.name
                if task_value_name in temp.values():
                    error_msg = "Task \"%s\" is set more than once " % task_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[task.id] = task_value_name
            return temp

    @api.multi
    @api.constrains('actualtask_ids')
    def _constrains_actualmastertask_id(self):
        self.ensure_one()
        if self.actualtask_ids:
            temp={}
            for task in self.actualtask_ids:
                task_value_name = task.mastertask_id.name
                if task_value_name in temp.values():
                    error_msg = "Task \"%s\" is set more than once " % task_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[task.id] = task_value_name
            return temp

    @api.multi
    @api.constrains('plannedpart_ids')
    def _constrains_plannedsparepart_id(self):
        self.ensure_one()
        if self.plannedpart_ids:
            temp={}
            for part in self.plannedpart_ids:
                part_value_name = part.product_id.name
                if part_value_name in temp.values():
                    error_msg = "Product Part \"%s\" is set more than once " % part_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[part.id] = part_value_name
            return temp

    @api.multi
    @api.constrains('actualpart_ids')
    def _constrains_actualsparepart_id(self):
        self.ensure_one()
        if self.actualpart_ids:
            temp={}
            for part in self.actualpart_ids:
                part_value_name = part.product_id.name
                if part_value_name in temp.values():
                    error_msg = "Product Part \"%s\" is set more than once " % part_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[part.id] = part_value_name
            return temp

    @api.multi
    @api.constrains('plannedtools_ids')
    def _constrains_plannedtools_id(self):
        self.ensure_one()
        if self.plannedtools_ids:
            temp={}
            for tools in self.plannedtools_ids:
                tools_value_name = tools.asset_id.name
                if tools_value_name in temp.values():
                    error_msg = "Tools or Equipment \"%s\" is set more than once " % tools_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[tools.id] = tools_value_name
            return temp

    @api.multi
    @api.constrains('actualtools_ids')
    def _constrains_actualtools_id(self):
        self.ensure_one()
        if self.actualtools_ids:
            temp={}
            for tools in self.actualtools_ids:
                tools_value_name = tools.asset_id.name
                if tools_value_name in temp.values():
                    error_msg = "Tools or Equipment \"%s\" is set more than once " % tools_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[tools.id] = tools_value_name
            return temp

    @api.multi
    @api.constrains('employeeline_ids')
    def _constrains_employee_id(self):
        if self.employeeline_ids:
            temp={}
            for employee in self.employeeline_ids:
                employee_value_name = employee.employee_id.name
                if employee_value_name in temp.values():
                    error_msg = "Employee \"%s\" is set more than once " % employee_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[employee.id] = employee_value_name
            return temp

    @api.multi
    @api.constrains('employeelineactual_ids')
    def _constrains_actualemployee_id(self):
        self.ensure_one()
        if self.employeelineactual_ids:
            temp={}
            for employee in self.employeelineactual_ids:
                employee_value_name = employee.employee_id.name
                if employee_value_name in temp.values():
                    error_msg = "Employee \"%s\" is set more than once " % employee_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[employee.id] = employee_value_name
            return temp

    @api.multi
    @api.constrains('employeeline_ids')
    def _constraint_employee_value(self):
        if self.employeeline_ids:
            temp = 0
            for manpower in self.plannedtask_ids:
                plannedmanpower = manpower.planned_manpower
                temp += plannedmanpower
            if len(self.employeeline_ids) > temp:
                error_msg = "Employee is set not more than Planned Manpower"
                raise exceptions.ValidationError(error_msg)
            elif len(self.employeeline_ids) < temp:
                error_msg = "Employee is set not more less than Planned Manpower"
                raise exceptions.ValidationError(error_msg)



    #---------------------------------------------------------------------------------------------


    #new API
    @api.multi
    def test_if_parts(self):
        #constraint for Maintenance type and priority
        for order in self:
            if order.typetask_id.id == False:
                error_msg = "Maintenance Type Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if order.code_id.id == False:
                error_msg = "Priority Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if order.type_service_handling == "1":
                countLineEmployee = 0
                countLinePlannedpart = 0
                countLinePlannedtask = 0
                countLinePlannedtools = 0
                for itemline in self:
                    countLineEmployee += len(itemline.employeeline_ids)
                    countLinePlannedpart += len(itemline.plannedpart_ids)
                    countLinePlannedtask += len(itemline.plannedtask_ids)
                    countLinePlannedtools += len(itemline.plannedtools_ids)
                if countLinePlannedtask == 0:
                    error_msg = "Tab Planned Operations in Tab Planning Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                if countLineEmployee == 0:
                    error_msg = "Tab Planned Labor's in Tab Planning Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                if countLinePlannedpart == 0:
                    error_msg = "Tab Planned Sparepart in Tab Planning Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                if countLinePlannedtools == 0:
                    error_msg = "Tab Planned Tools in Tab Planning Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                if self.code_id.name == 'High' or self.code_id.name == 'high' or self.code_id.name == 'Tinggi' or self.code_id.name == 'tinggi':
                    #change state in fleet_vehicle to breakdown
                    vehicle_id = self.env['asset.asset'].search([('id','=',self.asset_id.id)]).fleet_id.id
                    state_id = self.env['fleet.vehicle'].search([('id','=',vehicle_id)]).maintenance_state_id.id
                    fleet_id = self.asset_id.fleet_id.id

                    #change state to breakdown in fleet.vehicle
                    self.env['fleet.vehicle'].search([('id','=',vehicle_id)])\
                            .write({'maintenance_state_id': 18})

                    #change state to breakdown in asset.asset
                    self.env['asset.asset'].search([('type_asset','=','1'),('fleet_id.id','=',fleet_id)])\
                        .write({'maintenance_state_id': 18})

                if self.code_id.name == 'Normal' or self.code_id.name == 'normal' or self.code_id.name == 'sedang' or self.code_id.name == 'Sedang':
                    #change state in fleet_vehicle to maintenance
                    vehicle_id = self.env['asset.asset'].search([('id','=',self.asset_id.id)]).fleet_id.id
                    state_id = self.env['fleet.vehicle'].search([('id','=',vehicle_id)]).maintenance_state_id.id
                    fleet_id = self.asset_id.fleet_id.id

                    #change state to maintenance in fleet.vehicle
                    self.env['fleet.vehicle'].search([('id','=',vehicle_id)])\
                            .write({'maintenance_state_id': 20})

                    #change state to maintenance in asset.asset
                    self.env['asset.asset'].search([('type_asset','=','1'),('fleet_id.id','=',fleet_id)])\
                        .write({'maintenance_state_id': 20})

                if self.code_id.name == 'Low' or self.code_id.name == 'low' or self.code_id.name == 'Rendah' or self.code_id.name == 'rendah':
                    #change state in fleet_vehicle to Repair
                    vehicle_id = self.env['asset.asset'].search([('id','=',self.asset_id.id)]).fleet_id.id
                    state_id = self.env['fleet.vehicle'].search([('id','=',vehicle_id)]).maintenance_state_id.id
                    fleet_id = self.asset_id.fleet_id.id

                    #change state to Repair in fleet.vehicle
                    self.env['fleet.vehicle'].search([('id','=',vehicle_id)])\
                            .write({'maintenance_state_id': 19})

                    #change state to Repair in asset.asset
                    self.env['asset.asset'].search([('type_asset','=','1'),('fleet_id.id','=',fleet_id)])\
                        .write({'maintenance_state_id': 19})

            if order.type_service_handling == "2":
                countLineExternal = 0
                for itemexternalline in self:
                    countLineExternal += len(itemexternalline.serviceexternal_ids)
                if countLineExternal == 0:
                    error_msg = "Tab External Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                for external in self.serviceexternal_ids :
                    #validation row in service external Tab
                    if external.amount == 0 :
                            error_msg = "Field Total Price Must be Filled"
                            raise exceptions.ValidationError(error_msg)
                    if external.date != self.env['mro.order'].search([('id','=',external.owner_id)]).date_planned:
                            error_msg = "Field Date Must be Match With Date in Maintenance Order"
                            raise exceptions.ValidationError(error_msg)
                    if external.vendor_id.id == False:
                            error_msg = "Field Vendor Must be Filled"
                            raise exceptions.ValidationError(error_msg)

                if self.code_id.name == 'High' or self.code_id.name == 'high' or self.code_id.name == 'Tinggi' or self.code_id.name == 'tinggi':
                    #change state in fleet_vehicle to breakdown
                    vehicle_id = self.env['asset.asset'].search([('id','=',self.asset_id.id)]).fleet_id.id
                    state_id = self.env['fleet.vehicle'].search([('id','=',vehicle_id)]).maintenance_state_id.id
                    fleet_id = self.asset_id.fleet_id.id
                    self.env['fleet.vehicle'].search([('id','=',vehicle_id)])\
                            .write({'maintenance_state_id': 18})

                    #change state to Breakdown in asset.asset
                    self.env['asset.asset'].search([('type_asset','=','1'),('fleet_id.id','=',fleet_id)])\
                        .write({'maintenance_state_id': 18})

                if self.code_id.name == 'Normal' or self.code_id.name == 'normal' or self.code_id.name == 'sedang' or self.code_id.name == 'Sedang':
                    #change state in fleet_vehicle to Maintenance
                    vehicle_id = self.env['asset.asset'].search([('id','=',self.asset_id.id)]).fleet_id.id
                    state_id = self.env['fleet.vehicle'].search([('id','=',vehicle_id)]).maintenance_state_id.id
                    fleet_id = self.asset_id.fleet_id.id
                    self.env['fleet.vehicle'].search([('id','=',vehicle_id)])\
                            .write({'maintenance_state_id': 20})

                    #change state to Maintenance in asset.asset
                    self.env['asset.asset'].search([('type_asset','=','1'),('fleet_id.id','=',fleet_id)])\
                        .write({'maintenance_state_id': 20})

                if self.code_id.name == 'Low' or self.code_id.name == 'low' or self.code_id.name == 'Rendah' or self.code_id.name == 'rendah':
                    #change state in fleet_vehicle to Repair
                    vehicle_id = self.env['asset.asset'].search([('id','=',self.asset_id.id)]).fleet_id.id
                    state_id = self.env['fleet.vehicle'].search([('id','=',vehicle_id)]).maintenance_state_id.id
                    fleet_id = self.asset_id.fleet_id.id
                    self.env['fleet.vehicle'].search([('id','=',vehicle_id)])\
                            .write({'maintenance_state_id': 19})

                    #change state to Repair in asset.asset
                    self.env['asset.asset'].search([('type_asset','=','1'),('fleet_id.id','=',fleet_id)])\
                        .write({'maintenance_state_id': 19})
            super(InheritMroOrder,self).test_if_parts()

    @api.multi
    def action_done(self):
        for order in self:
            if order.reconcil_id.id == False:
                error_msg = "Reconcil Field Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if order.image == None:
                    error_msg = "Accident Image Must be Filled"
                    raise exceptions.ValidationError(error_msg)
            if order.type_service_handling == "1":
                countLineEmployee = 0
                countLineActualpart = 0
                countLineActualtask = 0
                countLineActualtools = 0
                for itemLine in self:
                    countLineActualtools += len(itemLine.actualtools_ids)
                    countLineActualpart += len(itemLine.actualtask_ids)
                    countLineActualtask += len(itemLine.actualpart_ids)
                    countLineEmployee += len(itemLine.mecanictimesheet_ids)
                if countLineActualtask == 0:
                    error_msg = "Tab Actual Operations in Tab Actual Task Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                if countLineActualpart == 0:
                    error_msg = "Tab Actual Sparepart in Tab Actual Task Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                if countLineEmployee == 0:
                    error_msg = "Tab Mechanic Timesheet's in Tab Actual Task Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                if countLineActualtools == 0:
                    error_msg = "Tab Actual Tools Must be Filled"
                    raise exceptions.ValidationError(error_msg)
            if self.reconcil_id.name == 'Fixed Completely' or self.reconcil_id.name == 'fixed Completely' \
                    or self.reconcil_id.name == 'Fixed completely' or self.reconcil_id.name == 'fixed completely' \
                    or self.reconcil_id.name == 'Selesai' or self.reconcil_id.name == 'selesai' \
                    or self.reconcil_id.name == 'Finished' or self.reconcil_id.name == 'finished' \
                    or self.reconcil_id.name == 'Done' or self.reconcil_id.name == 'done':

                #change state in fleet_vehicle to Operable

                vehicle_id = self.env['asset.asset'].search([('id','=',self.asset_id.id)]).fleet_id.id
                state_id = self.env['fleet.vehicle'].search([('id','=',vehicle_id)]).maintenance_state_id.id
                fleet_id = self.asset_id.fleet_id.id
                self.env['fleet.vehicle'].search([('id','=',vehicle_id)])\
                        .write({'maintenance_state_id': 21})

                #change state to Operable in asset.asset
                self.env['asset.asset'].search([('type_asset','=','1'),('fleet_id.id','=',fleet_id)])\
                        .write({'maintenance_state_id': 21})

            if self.reconcil_id.name == 'Fixed Partially' or self.reconcil_id.name == 'Fixed partially' \
                    or self.reconcil_id.name == 'fixed Partially' or self.reconcil_id.name == 'fixed partially' \
                    or self.reconcil_id.name == 'Selesai sebagian' or self.reconcil_id.name == 'selesai sebagian' \
                    or self.reconcil_id.name == 'Selesai Sebagian':
                #change state in fleet_vehicle to Operable

                vehicle_id = self.env['asset.asset'].search([('id','=',self.asset_id.id)]).fleet_id.id
                state_id = self.env['fleet.vehicle'].search([('id','=',vehicle_id)]).maintenance_state_id.id
                fleet_id = self.asset_id.fleet_id.id
                self.env['fleet.vehicle'].search([('id','=',vehicle_id)])\
                        .write({'maintenance_state_id': 21})

                #change state to Operable in asset.asset
                self.env['asset.asset'].search([('type_asset','=','1'),('fleet_id.id','=',fleet_id)])\
                        .write({'maintenance_state_id': 21})

            if self.reconcil_id.name == 'Not Posible To Fix' or self.reconcil_id.name == 'Not posible to fix' \
                    or self.reconcil_id.name == 'tidak Selesai' or self.reconcil_id.name == 'Tidak Selesai' \
                    or self.reconcil_id.name == 'tidak selesai':

                #change state in fleet_vehicle to breakdown

                vehicle_id = self.env['asset.asset'].search([('id','=',self.asset_id.id)]).fleet_id.id
                state_id = self.env['fleet.vehicle'].search([('id','=',vehicle_id)]).maintenance_state_id.id
                fleet_id = self.asset_id.fleet_id.id
                self.env['fleet.vehicle'].search([('id','=',vehicle_id)])\
                        .write({'maintenance_state_id': 18})

                #change state to Breakdown in asset.asset
                self.env['asset.asset'].search([('type_asset','=','1'),('fleet_id.id','=',fleet_id)])\
                        .write({'maintenance_state_id': 18})
            super(InheritMroOrder,self).action_done()

    @api.multi
    @api.onchange('employeelineactual_ids','actualtask_ids')
    def _onchange_actual_manpower(self):

        for item in self:
            countemployee = len(item.employeelineactual_ids)
            for actual in self.actualtask_ids:
                actual.write({'actual_manpower' : countemployee})

    @api.multi
    @api.onchange('actualtask_ids','mecanictimesheet_ids')
    def _onchange_actual_hours(self):
        for item in self:
            if len(item.mecanictimesheet_ids) >= 1:
                sumtotaltime = 0
                for actual in item.actualtask_ids:
                    for delta_time in item.mecanictimesheet_ids:
                        if delta_time.mastertask_id == actual.mastertask_id:
                            calculate_endtime = round(delta_time.end_time%1*0.6,2)+(delta_time.end_time-delta_time.end_time%1)
                            calculate_starttime = round(delta_time.start_time%1*0.6,2)+(delta_time.start_time-delta_time.start_time%1)
                            totaltime = calculate_endtime-calculate_starttime
                            sumtotaltime += totaltime
                    actual.write({'actual_hour':sumtotaltime})
            if len(item.mecanictimesheet_ids) < 1:
                for actual in item.actualtask_ids:
                    actual.write({'actual_hour':0})

    @api.multi
    @api.onchange('category_unit_id','asset_id')
    def _onchange_category_unit_id(self):
        for record in self:
            if record.asset_id:
                record.category_unit_id = record.asset_id.category_unit_id

    @api.multi
    @api.depends('category_name','asset_id')
    def _onchange_category_unit_name(self):
        for record in self:
            if record.asset_id:
                record.category_name = record.asset_id.category_name

    @api.multi
    def unlink(self):
        self.env['estate.timesheet.activity.transport'].search([('owner_id','=',self.id)]).unlink()
        return super(InheritMroOrder, self).unlink()

    @api.multi
    def action_ready(self):
        self.do_create_actualtask()
        self.do_create_actualsparepart()
        self.do_create_actualequipment()
        self.do_create_actualeemployee()
        self.write({'state': 'ready'})

    @api.multi
    def do_create_actualtask(self):
        task_data = False
        for task in self.env['estate.workshop.plannedtask'].search([('mro_id.id','=',self.id)]):
            task_data = {
                'name':'Actual Task',
                'mastertask_id': task.mastertask_id.id,
                'planned_hour': task.planned_hour,
                'planned_manpower': task.planned_manpower,
                'mro_id' : task.mro_id.id
            }
            self.env['estate.workshop.actualtask'].create(task_data)
        return True

    @api.multi
    def do_create_actualsparepart(self):
        part_data = False
        for part in self.env['estate.workshop.planned.sparepart'].search([('owner_id','=',self.id)]):
            part_data = {
                'name' : 'Actual Sparepart',
                'product_id' :  part.product_id.id,
                'qty_product' : part.qty_product,
                'uom_id' : part.uom_id.id,
                'qty_available' : part.qty_available,
                'owner_id' : part.owner_id
            }
            self.env['estate.workshop.actual.sparepart'].create(part_data)
        return True

    @api.multi
    def do_create_actualequipment(self):
        tool_data = False
        for tool in self.env['estate.workshop.plannedequipment'].search([('mro_id','=',self.id)]):
            tool_data = {
                'name':'Actual Equipment',
                'asset_id' : tool.asset_id.id,
                'ownership' : tool.ownership,
                'uom_id' : tool.uom_id.id,
                'unit_plan' : tool.unit_plan,
                'description' : tool.description,
                'mro_id' : tool.mro_id
            }
            self.env['estate.workshop.actualequipment'].create(tool_data)
        return True

    @api.multi
    def do_create_actualeemployee(self):
        employee_data = False
        for employee in self.env['estate.workshop.employeeline'].search([('mro_id','=',self.id)]):
            employee_data = {
                'employee_id' : employee.employee_id.id,
                'mro_id' : employee.mro_id
            }
            self.env['estate.workshop.employeeline.actual'].create(employee_data)
        return True

    @api.multi
    @api.onchange('plannedtask_ids','actualtask_ids')
    def _onchange_plannedtask_id(self):
        if self.state == 'draft':
            for owner in self.plannedtask_ids:
                owner.owner_id = self.owner_id
        if self.state == 'ready':
            for owner in self.actualtask_ids:
                owner.owner_id = self.owner_id

    @api.multi
    @api.onchange('owner_id','asset_id')
    def _onchange_owner_id(self):
        if self.asset_id :
            self.owner_id = self.asset_id.id

    #onchange
    @api.multi
    @api.onchange('asset_id','type_service')
    def _onchange_type_service(self):
        if self.asset_id == True:
            self.type_service = self.asset_id.type_asset

    # @api.multi
    def process_scheduler_workshop(self, cr, uid, context=None):
        #execute generate MO preventive scheduler
        cr.execute('select create_mo_preventive();')
        line = cr.fetchone()[0]
















