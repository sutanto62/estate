from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal
import time
import re

# class MasterTimesheet(models.Model):
#
#     _name = 'estate.timesheet'
#     _description = "Estate Master Time Sheet for Activity"

class TimesheetActivityTransport(models.Model):

    _name = 'estate.timesheet.activity.transport'
    _description = "Estate Master Time Sheet for Activity Transport"

    id = fields.Integer()
    name=fields.Char("Timesheet Activity Tranport")
    date_activity_transport = fields.Date("Date activity Transport")
    owner_id = fields.Integer()
    employee_id = fields.Many2one('hr.employee','Employee ID',store=True)
    dc_type = fields.Char()
    uom_id = fields.Many2one('product.uom',store=True)
    unit = fields.Float('unit per activity',digits=(2,2),store=True)
    vehicle_id = fields.Many2one('fleet.vehicle',store=True)
    activity_id = fields.Many2one('estate.activity',store=True,domain=[('activity_type','=','vehicle'),('type','=','normal')])
    partner_id=fields.Many2one('res.partner')
    timesheet_activity_code = fields.Char()
    start_km = fields.Float(digits=(2,2),store=True)
    end_km = fields.Float(digits=(2,2),store=True)
    total_distance = fields.Float(digits=(2,2),compute='_compute_total_distance',store=True)
    start_location = fields.Many2one('estate.block.template',store=True)
    end_location = fields.Many2one('estate.block.template',store=True)
    distance_location = fields.Float('Distance Location',store=True,compute='_onchange_distance_location')
    start_time = fields.Float(digits=(2,2))
    end_time = fields.Float(digits=(2,2))
    total_time = fields.Float(digits=(2,2),compute='_compute_total_time')
    comment = fields.Text()
    type_transport = fields.Selection([
        ('ntrip', 'Non Trip'),
        ('trip', 'Trip'),
        ], string="Type",store=True,compute='change_type_transport')
    state=fields.Selection([('draft','Draft'),
        ('confirmed', 'Confirmed'),('approved1','First Approval'),('approved2','Second Approval'),
        ('done', 'Done'),('cancel','Cancel'),('reject','Reject')],string="Activity Timesheet State")

    #onchange ALL

    @api.multi
    @api.onchange('start_location')
    def _onchange_end_location(self):
        #use to onchange domain end_location same as master location path
        if self:
            if self.start_location:
                arrEndlocation=[]
                arrStartlocation = []
                temp=[]
                endlocation=self.env['path.location'].search([('start_location.id','=',self.start_location.id)])
                allLocation=self.env['estate.block.template'].search([])
                for record in allLocation:
                    temp.append(record.id)
                for record in endlocation:
                        arrStartlocation.append(record.start_location.id)
                if self.start_location.id in arrStartlocation:
                    for record in endlocation:
                        arrEndlocation.append(record.end_location.id)
                    return {
                    'domain':{
                        'end_location':[('id','in',arrEndlocation)]
                    }
                }
                elif self.start_location.id not in arrStartlocation:
                    return {
                    'domain':{
                        'end_location':[('id','in',temp)]
                         }
                    }
                else:
                    return {
                    'domain':{
                        'end_location':[('id','in',temp)]
                         }
                    }

    @api.multi
    @api.onchange('type_transport')
    def _onchange_unit(self):
        if self.type_transport =='trip':
            self.unit = 1
        elif self.type_transport == 'ntrip':
            self.unit = 0

    @api.multi
    @api.onchange('activity_id')
    def _onchange_uom(self):
        if self.activity_id:
            self.uom_id = self.activity_id.uom_id


    @api.multi
    @api.depends('activity_id')
    def change_type_transport(self):
        for item in self:
            if item.activity_id:
                item.type_transport = item.activity_id.type_transport

    @api.multi
    @api.depends('distance_location','end_location','start_location')
    def _onchange_distance_location(self):
        #to change distance location same master path location
        for item in self:
            if item.start_location and item.end_location:
                arrDistance = 0
                distancelocation = item.env['path.location'].search([
                    ('start_location.id','=',item.start_location.id),('end_location.id','=',item.end_location.id)])
                for c in distancelocation:
                    arrDistance += c.distance_location
                item.distance_location = arrDistance
        return True

    @api.multi
    @api.onchange('employee_id')
    def _onchange_driver(self):
        arrDriver = []
        if self:
            hrjob = self.env['hr.job'].search([('name','=','sopir')],limit = 1).id
            driver = self.env['hr.employee'].search([('job_id.id','=',hrjob)])
            for d in driver:
                arrDriver.append(d.id)
        return {
                'domain':{
                    'employee_id':[('id','in',arrDriver)]
                }
        }

    @api.multi
    @api.onchange('vehicle_id')
    def onchange_vehicle(self):
        arrVehicletransport =[]
        if self:
            if self.dc_type == '1':# dc type 1 refer to seed do
                dotransportir = self.env['estate.nursery.dotransportir'].search([('seeddo_id.id','=',self.owner_id)])
                for vehicle in dotransportir:
                    arrVehicletransport.append(vehicle.estate_vehicle_id.id)
                return {
                    'domain':{
                        'vehicle_id':[('id','in',arrVehicletransport)]
                        }
                    }
            else :
                vehicle=self.env['fleet.vehicle'].search([('maintenance_state_id.id','=',21)])
                for v in vehicle:
                    arrVehicletransport.append(v.id)
                return {
                    'domain':{
                        'vehicle_id':[('id','in',arrVehicletransport)]
                        }
                    }
    @api.multi
    @api.onchange('dc_type')
    def _onchange_dc_type(self):
        if self:
            self.dc_type = 3

    #Computed ALL
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

    @api.multi
    @api.depends('start_km','end_km')
    def _compute_total_distance(self):
        #to Compute total Distance
        for item in self:
            if item.end_km and item.start_km:
                item.total_distance = item.end_km - item.start_km


    #Constraint ALL

    @api.multi
    @api.constrains('start_km','end_km')
    def _constraint_startkm_endkm(self):

        for item in self:
            if item.end_km < item.start_km:
                error_msg="End KM  %s is set more less than Start KM %s " %(self.end_km,self.start_km)
                raise exceptions.ValidationError(error_msg)
            return True


    @api.multi
    @api.constrains('start_time','end_time')
    def _constraint_starttime_endtime(self):
        Max = float(24.0)
        Min = float(0.0)
        if self:
            if self.start_time < Min:
                error_msg = "Start Time Not More Less Than 00:00"
                raise exceptions.ValidationError(error_msg)
            if self.end_time < Min:
                error_msg = "End Time Not More Less Than 00:00"
                raise exceptions.ValidationError(error_msg)
            if self.start_time >  Max:
                error_msg = "Start Time Not More Than 24:00"
                raise exceptions.ValidationError(error_msg)
            if self.end_time > Max :
                error_msg = "End Time Not More Than 24:00"
                raise exceptions.ValidationError(error_msg)
            if self.end_time < self.start_time:
                calculate_endtime = round(self.end_time%1*0.6,2)+(self.end_time-self.end_time%1)
                calculate_starttime = round(self.start_time%1*0.6,2)+(self.start_time-self.start_time%1)
                error_msg="End Time  %s is set more less than Start Time %s " %(calculate_endtime,calculate_starttime)
                raise exceptions.ValidationError(error_msg)
            return True

    #state for Cleaving
    @api.multi
    def action_draft(self):

        self.ensure_one()
        self.state = 'draft'

    @api.multi
    def action_confirmed(self):

        self.ensure_one()
        self.state = 'confirmed'

    @api.multi
    def action_approved1(self):

        self.ensure_one()
        self.state = 'approved1'

    @api.multi
    def action_approved2(self):

        self.ensure_one()
        self.state = 'approved2'

    @api.multi
    def action_approved(self):

        self.ensure_one()
        self.state = 'done'


class MasterPath(models.Model):

    _name = 'path.location'
    _description = "Estate Master path location"

    name=fields.Char("Master Path")
    distance_location = fields.Float('Distance Location',digits=(2,2))
    factor_id = fields.Many2one('master.factor.multiple',domain=[('type','=','2')])
    path_price = fields.Float('Standard Price',digits=(2,2))
    start_location=fields.Many2one('estate.block.template', "Plot")
    end_location=fields.Many2one('estate.block.template', "Plot")
    comment = fields.Text()


class MasterFactorMultiple(models.Model):

    _name = 'master.factor.multiple'
    _description = "Master Fator Multiple for activity"

    name=fields.Char("Master Factor")
    parameter_id=fields.Many2one('estate.parameter')
    parameter_value_id = fields.Many2one("estate.parameter.value")
    type = fields.Selection([('1', 'Human'), ('2', 'Vehicle')],
                             string="Parameter type",
                             help="Define use factor.")
    factor_multiple = fields.Float("Factor Multiple",digits=(2,2))

    #onchange
    @api.multi
    @api.onchange('parameter_id','parameter_value_id')
    def onchange_parameter_value(self):
        #to domain parameter value in parameter id
        arrParameter = []
        if self:
            if self.parameter_id:
                parameter = self.env['estate.parameter.value'].search([('parameter_id.id','=',self.parameter_id.id)])
                for parameter in parameter:
                    arrParameter.append(parameter.parameter_id.id)
                return {
                    'domain' : {
                            'parameter_value_id':[('parameter_id.id','in',arrParameter)]
                            }
                    }

class FormulaPremiActivityVehicle(models.Model):

    _name = 'master.formula.activity.vehicle'
    _description = "Create formula to compute premi for driver , activity , and vehicle"

    name=fields.Char()
    formula_name = fields.Char('Formula name')
    range_start = fields.Float('Range Distance Start' , digits=(2,2))
    range_end = fields.Float('Range Distance End' , digits=(2,2))
    type_handling = fields.Selection([('1', 'Single Handling'), ('2', 'Double Handling')],
                             string="Handling type",
                             help="Define use factor.")
    type_day = fields.Selection([('1', 'Ordinary Day'), ('2', 'Friday')],
                             string="Day type",
                             help="Define use factor.")
    basis = fields.Integer('Basis(Trip)')
    premi_base = fields.Float('Basis Premi',digits=(2,2))
    category_unit_id = fields.Many2one('master.category.unit',domain=([('type','=','1')]))
    job_id = fields.Many2one('hr.job',domain=([('department_id','=',11)]))
    use_start = fields.Date('Use Start')
    use_end = fields.Date('Use End')

class ViewTimesheetPremi(models.Model):

    _name='v.timesheet.premi'
    _description = "Timesheets by Activity"
    _auto = False
    _order='date_activity_transport'

    id = fields.Integer('id')
    date_activity_transport = fields.Date('date')
    employee_id = fields.Many2one('hr.employee')
    start_location = fields.Many2one('estate.block.template')
    end_location = fields.Many2one('estate.block.template')
    total_trip = fields.Integer()
    total_productivity = fields.Integer()
    basis = fields.Integer()
    premi = fields.Float()

    def init(self, cr):
        cr.execute("""create or replace view v_timesheet_premi as
           select
                pl.id,
                ts.*,
                fa.basis,
                case when ((ts.total_trip - fa.basis) * fa.premi_base) < 0 then 0 else ((ts.total_trip - fa.basis) * fa.premi_base) end as premi
            from
                (
                    select
                        ts.date_activity_transport,
                        ts.employee_id,
                        ts.start_location,
                        ts.end_location,
                        count(ts.id) total_trip,
                        sum(ts.unit) total_productivity
                    from
                        estate_timesheet_activity_transport ts
                    group by
                        ts.date_activity_transport, ts.employee_id, ts.start_location, ts.end_location
                ) ts
                inner join path_location pl
                on ts.start_location = pl.start_location and ts.end_location = pl.end_location
                inner join
                master_formula_activity_vehicle fa
                on pl.distance_location >= fa.range_start and pl.distance_location <= fa.range_end""")





