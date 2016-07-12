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

    timesheet_ids = fields.One2many('estate.timesheet.activity.transport','owner_id','Timesheet ids')

    @api.multi
    @api.constrains('timesheet_ids')
    def _constraints_timesheet(self):
        #constraint timesheet for quantity unit not more than bpb
        self.ensure_one()
        qty_unit = 0
        qty_seed = 0
        if self.timesheet_ids:
            for timesheet in self.timesheet_ids:
                qty_unit += timesheet.unit
            for bpb in self.request_ids:
                qty_seed += bpb.total_qty_pokok
            if qty_unit > qty_seed:
                error_msg = "Unit not more than \"%s\" in qty total BPB" % qty_seed
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
                error_msg = "Date not more than \"%s\" in Date move" % self.date_request
                raise exceptions.ValidationError(error_msg)
            elif date < self.date_request:
                error_msg = "Date must be same \"%s\" in Date move" % self.date_request
                raise exceptions.ValidationError(error_msg)

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
                error_msg = "Unit not more than \"%s\" in qty move" % self.qty_move
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
                error_msg = "Date not more than \"%s\" in Date move" % self.date_transfer
                raise exceptions.ValidationError(error_msg)
            elif date < self.date_transfer:
                error_msg = "Date must be same \"%s\" in Date move" % self.date_transfer
                raise exceptions.ValidationError(error_msg)

    @api.multi
    @api.constrains('vehicle_timesheet_ids')
    def _constraints_line_timesheet_mustbe_filled(self):
        #Constraint Line activity_Transfer must be filled
            countActivity = 0
            for item in self:
                countActivity += len(item.vehicle_timesheet_ids)
            if countActivity == 0 :
                error_msg = "Line Activity Must be filled"
                raise exceptions.ValidationError(error_msg)