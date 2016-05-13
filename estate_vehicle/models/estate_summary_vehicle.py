from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal

class MasterStructureCostVehicle(models.Model):

    _name = "estate.vehicle.master.cost"
    _description = "Master for cost estate vehicle"


    name=fields.Char()
    vehicle_id = fields.Many2one('fleet.vehicle')
    timesheet_id = fields.Many2one('estate.timesheet.activity.transport')
    date_master = fields.Date('Date Master')
    total_wage = fields.Float('Total Cost Wage',digits=(2,2))
    total_fuel = fields.Float('Total CostFuel',digits=(2,2))
    total_oil = fields.Float('Total Cost Oil',digits=(2,2))
    total_sparepart = fields.Float('Total Cost Sparepart',digits=(2,2))
    total_service = fields.Float('Total Cost Sercive',digits=(2,2))
    total_other_cost = fields.Float('Total Other Cost ',digits=(2,2))

class DetailCostVehicle(models.Model):

    _name="estate.vehicle.detail.cost"
    _description = "Detail for cost every month vehicle"


