from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
import time
import datetime
from openerp import tools

class InheritMaintenanceVehicle(models.Model):


    _inherit="fleet.vehicle"
    _description = "inherit information detail to fleet management"


    maintenance_state_id = fields.Many2one('asset.state','Asset State',domain=[('team','=','3')])
    maintenance_state_color = fields.Selection('State Color',related='maintenance_state_id.state_color')
    type_location_vehicle = fields.Selection([
        ('ro', 'RO'),
        ('estate', 'Estate'),
        ('ho', 'HO')], string="Type Location Vehicle",store=True)
    company_id = fields.Many2one('res.company','Company',store=True)

