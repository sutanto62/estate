from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal
import time
import re


class InheritSPB(models.Model):

    _inherit ='estate.nursery.seeddo'

    timesheet_ids = fields.One2many('estate.spb.vehicle.timesheet','owner_id','Timesheet ids')

    @api.multi
    @api.constrains('timesheet_ids')
    def _constraints_timesheet(self):
        #constraint timesheet for quantity unit not more than bpb
        qty_unit = 0
        qty_seed = 0
        if self.timesheet_ids:
            for timesheet in self.timesheet_ids:
                qty_unit += timesheet.unit
            for bpb in self.request_ids:
                qty_seed += bpb.total_qty_pokok
            if qty_unit > qty_seed:
                error_msg = "Qty Unit not more than \"%s\" in qty total BPB" % qty_seed
                raise exceptions.ValidationError(error_msg)
        return True

    @api.multi
    @api.constrains('timesheet_ids')
    def _constraint_date_timesheet(self):
        #constraint date in timesheet must be same in seed do
        self.ensure_one()
        if self.timesheet_ids:
            for vehicletimesheet in self.timesheet_ids:
                date = vehicletimesheet.date_activity_transport
            if date > self.date_request:
                error_msg = "Date Vehicle Timesheet not more than \"%s\" in Date Request" % self.date_request
                raise exceptions.ValidationError(error_msg)
            elif date < self.date_request:
                error_msg = "Date Vehicle Timesheet must be same \"%s\" in Date Request" % self.date_request
                raise exceptions.ValidationError(error_msg)

    @api.one
    def action_approved1(self):
        """Approved planting is validate 1."""
        countLineActivity = 0
        countLineVehicle = 0
        countLineTimesheet = 0
        countLineRequest = 0
        for itemline in self:
            countLineRequest += len(itemline.request_ids)
            countLineActivity += len(itemline.activityline_ids)
            countLineTimesheet += len(itemline.timesheet_ids)
            countLineVehicle += len(itemline.dotransportir_ids)
            if countLineActivity == 0:
                error_msg = "Tab BPB List Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if countLineActivity == 0:
                error_msg = "Tab Activity Transportir Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if countLineVehicle == 0:
                error_msg = "Tab Detail Transportir Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if countLineTimesheet == 0:
                error_msg = "Tab Vehicle Timesheet Must be Filled"
                raise exceptions.ValidationError(error_msg)
        super(InheritSPB,self).action_approved1()

    @api.multi
    @api.constrains('timesheet_ids')
    def _constraints_line_timesheet_ids(self):
        #Constraint Line Timesheet in planting must be filled
            countTimesheet = 0
            for item in self:
                countTimesheet += len(item.activityline_ids)
            if self.state == 'done':
                if countTimesheet == 0 :
                    error_msg = "Tab Vehicle Timesheet Must be filled"
                    raise exceptions.ValidationError(error_msg)

class SpbTimesheetVehicle(models.Model):

    _name = 'estate.spb.vehicle.timesheet'
    _inherits = {'estate.timesheet.activity.transport':'timesheet_id'}

    timesheet_id = fields.Many2one('estate.timesheet.activity.transport',ondelete='cascade',required=True)
    fleet_id = fields.Many2one('fleet.vehicle')


    @api.multi
    @api.onchange('fleet_id')
    def _onchange_vehicle_id(self):
        # on change vehicle id where status vehicle
        arrVehicle=[]
        if self:
            for item in self:
                vehicle=item.env['estate.nursery.dotransportir'].search([('seeddo_id.id','=',item.owner_id)])
                for vehicleid in vehicle:
                    arrVehicle.append(vehicleid.estate_vehicle_id.id)
                return {
                        'domain':{
                            'fleet_id':[('id','in',arrVehicle)]
                        }
                }

    @api.multi
    @api.onchange('vehicle_id','fleet_id')
    def _onchange_fleet_id(self):
        for item in self:
            if item.fleet_id:
                item.vehicle_id= item.fleet_id

    @api.multi
    @api.onchange('activity_id')
    def _onchange_activity_id(self):
        # on change activity id
        arrActivity=[]
        if self:
            for item in self:
                activity=item.env['estate.nursery.activityline'].search([('seeddo_id.id','=',item.owner_id)])
                for activityid in activity:
                    arrActivity.append(activityid.activity_id.id)
                return {
                        'domain':{
                            'activity_id':[('id','in',arrActivity)]
                        }
                }

    @api.multi
    @api.onchange('start_location')
    def _onchange_startlocation(self):
        #onchange start location same at BPB line
        arrStartLocation = []
        if self:
            for item in self:
                request = item.env['estate.nursery.request'].search([('seeddo_id','=',item.owner_id)])
                requestline = item.env['estate.nursery.requestline'].search([('request_id.id','=',request[0].id)])
                for startlocation in requestline:
                    arrStartLocation.append(startlocation.location_id.id)
                return {
                        'domain':{
                            'start_location':[('id','in',arrStartLocation)]
                        }
                }

    @api.multi
    @api.onchange('end_location')
    def _onchange_endlocation(self):
        #onchange end location same at BPB line
        arrEndLocation = []
        if self:
            for item in self:
                request = item.env['estate.nursery.request'].search([('seeddo_id','=',item.owner_id)])
                requestline = item.env['estate.nursery.requestline'].search([('request_id.id','=',request[0].id)])
                for Endlocation in requestline:
                    arrEndLocation.append(Endlocation.block_location_id.id)
                return {
                        'domain':{
                            'end_location':[('id','in',arrEndLocation)]
                        }
                }


class InheritTransfertoMN(models.Model):

    _inherit ='estate.nursery.transfermn'

    vehicle_timesheet_ids = fields.One2many('estate.timesheet.activity.transport','owner_id')

    @api.multi
    @api.constrains('vehicle_timesheet_ids')
    def _constraints_timesheet_unit(self):
        #constraint timesheet for quantity unit not more than qty move
        self.ensure_one()
        qty_unit = 0
        if self.vehicle_timesheet_ids:
            for timesheet in self.vehicle_timesheet_ids:
                qty_unit += timesheet.unit
            if qty_unit > self.qty_move:
                error_msg = "Qty Unit not more than \"%s\" in qty move" % self.qty_move
                raise exceptions.ValidationError(error_msg)
        return True

    @api.multi
    @api.constrains('vehicle_timesheet_ids')
    def _constraint_date_timesheet(self):
        #constraint date in move to mn must be same in time sheet ids
        self.ensure_one()
        if self.vehicle_timesheet_ids:
            for vehicletimesheet in self.vehicle_timesheet_ids:
                date = vehicletimesheet.date_activity_transport
            if date > self.date_transfer:
                error_msg = "Date Transfer not more than \"%s\" in Date move" % self.date_transfer
                raise exceptions.ValidationError(error_msg)
            elif date < self.date_transfer:
                error_msg = "Date Transfer must be same \"%s\" in Date move" % self.date_transfer
                raise exceptions.ValidationError(error_msg)

    @api.multi
    @api.constrains('vehicle_timesheet_ids')
    def _constraints_line_timesheet_mustbe_filled(self):
        #Constraint Line activity_Transfer must be filled
            countActivity = 0
            for item in self:
                countActivity += len(item.vehicle_timesheet_ids)
            if countActivity == 0 :
                error_msg = "Line Vehicle Information Must be filled"
                raise exceptions.ValidationError(error_msg)

class InheritFleet(models.Model):

    _inherit='fleet.vehicle'

    vehicle_type=fields.Selection([('1','Vehicle Internal'), ('2','Vehicle External')])
    employee_driver_id=fields.Many2one('hr.employee')