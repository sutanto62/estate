from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal


# class MasterTimesheet(models.Model):
#
#     _name = 'estate.timesheet'
#     _description = "Estate Master Time Sheet for Activity"

class TimesheetActivityTransport(models.Model):

    _name = 'estate.timesheet.activity.transport'
    _description = "Estate Master Time Sheet for Activity Transport"

    def _default_session(self):
        return self.env['estate.nursery.seeddo'].browse(self._context.get('active_id'))

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
    start_time = fields.Float(digits=(4,0))
    end_time = fields.Float(digits=(4,0))
    total_time = fields.Float(digits=(4,0),compute='_compute_total_time')
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
        if self:
            if self.start_time:
                startTime = self.start_time
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
    path_price = fields.Float('Standard Price',digits=(2,2))
    start_location=fields.Many2one('estate.block.template', "Plot")
    end_location=fields.Many2one('estate.block.template', "Plot")
    comment = fields.Text()
