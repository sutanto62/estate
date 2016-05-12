from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar




class NurseryVehicle(models.Model):

    _inherit="fleet.vehicle"
    _description = "inherit information detail to fleet management"

    no_vehicle=fields.Char('No Vehicle')
    vehicle_type=fields.Selection([('1','Vehicle Internal'), ('2','Vehicle External')])
    employee_driver_id=fields.Many2one('hr.employee')
    capacity_vehicle = fields.Integer('Capacity')
    status_vehicle = fields.Selection([('1','Available'), ('2','Breakdown')])







