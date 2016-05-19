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
    activity_id = fields.Many2one('estate.activity',store=True)
    partner_id=fields.Many2one('res.partner')
    timesheet_activity_code = fields.Char()
    start_location = fields.Many2one('estate.block.template',store=True)
    end_location = fields.Many2one('estate.block.template',store=True)
    distance_location = fields.Float('Distance Location',store=True)
    start_time = fields.Float(digits=(2,2))
    end_time = fields.Float(digits=(2,2))
    total_time = fields.Float(digits=(2,2),compute='_compute_total_time')
    comment = fields.Text()
    state=fields.Selection([('draft','Draft'),
        ('confirmed', 'Confirmed'),('approved1','First Approval'),('approved2','Second Approval'),
        ('done', 'Done')],string="Activity Timesheet State")

    #onchange ALL
    @api.multi
    @api.onchange('end_location')
    def _onchange_path_location(self):
        #use to onchange domain start location  same as master location path
        if self:
            arrStartlocation=[]
            startlocation=self.env['path.location'].search([])
            for a in startlocation:
                    arrStartlocation.append(a.start_location.id)
            return {
                'domain':{
                    'start_location':[('id','=',arrStartlocation)]
                }
        }

    @api.multi
    @api.onchange('start_location','end_location')
    def _onchange_end_location(self):
        #use to onchange domain end_location same as master location path
        if self:
            if self.start_location:
                arrEndlocation=[]
                endlocation=self.env['path.location'].search([('start_location.id','=',self.start_location.id)])
                for b in endlocation:
                    arrEndlocation.append(b.end_location.id)
                return {
                'domain':{
                    'end_location':[('id','in',arrEndlocation)]
                }
        }

    @api.multi
    @api.onchange('distance_location','end_location','start_location')
    def _onchange_distance_location(self):
        #to change distance location same master path location
        if self:
            if self.start_location and self.end_location:
                arrDistance = 0
                distancelocation = self.env['path.location'].search([
                    ('start_location.id','=',self.start_location.id),('end_location.id','=',self.end_location.id)])
                for c in distancelocation:
                    arrDistance += c.distance_location
                self.distance_location = arrDistance

    @api.multi
    @api.onchange('employee_id')
    def _onchange_driver(self):
        arrDriver = []
        if self:
            hrjob = self.env['hr.job'].search([('name','=','Driver')],limit = 1).id
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
                vehicle=self.env['fleet.vehicle'].search([('status_vehicle','=','1')])
                for v in vehicle:
                    arrVehicletransport.append(v.id)
                return {
                    'domain':{
                        'vehicle_id':[('id','in',arrVehicletransport)]
                        }
                    }

    #Sequence Recovery code
    # def create(self, cr, uid, vals, context=None):
    #     vals['timesheet_activity_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.timesheet.activity.transport')
    #     res=super(TimesheetActivityTransport, self).create(cr, uid, vals)
    #     return res

    #Computed ALL
    @api.multi
    @api.depends('start_time','end_time','total_time')
    def _compute_total_time(self):
        self.ensure_one()
        #to compute total_time
        if self:
            if self.start_time and self.end_time:
                self.total_time = self.end_time - self.start_time
        return True

    #state for Cleaving
    @api.one
    def action_draft(self):
        """Set Selection State to Draft."""
        self.state = 'draft'

    @api.one
    def action_confirmed(self):
        """Set Selection state to Confirmed."""
        self.state = 'confirmed'

    @api.one
    def action_approved1(self):
        """Set Selection state to Confirmed."""
        self.state = 'approved1'

    @api.one
    def action_approved2(self):
        """Set Selection state to Confirmed."""
        self.state = 'approved2'

    @api.one
    def action_approved(self):
        """Approved Selection is planted Seed to batch."""
        # self.action_receive()
        self.state = 'done'

    # @api.one
    # def action_receive(self):
    #     self.action_move()
    #
    # @api.one
    # def action_move(self):



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
    category_unit_id = fields.Many2one('master.category.unit')
    job_id = fields.Many2one('hr.job')
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
                ((ts.total_trip - fa.basis) * fa.premi_base) as premi
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
