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

    @api.multi
    def write(self,context):
        #Triger to change asset.state in asset.asset
        if self.maintenance_state_id:
                vehicle_id = self.env['fleet.vehicle'].search([('id','=',self.id)]).id
                vehicle_state_id = self.env['fleet.vehicle'].search([('id','=',vehicle_id)]).maintenance_state_id.id
                if vehicle_state_id == 21:
                    state = self.env['asset.state'].search([('id','=',vehicle_state_id)]).id
                    state_id = state - 3
                    self.env['asset.asset'].search([('type_asset','=','1'),('fleet_id.id','=',vehicle_id)])\
                        .write({'maintenance_state_id': state_id})
                if vehicle_state_id == 18:
                    state = self.env['asset.state'].search([('id','=',vehicle_state_id)]).id
                    state_id = state + 1
                    self.env['asset.asset'].search([('type_asset','=','1'),('fleet_id.id','=',vehicle_id)])\
                        .write({'maintenance_state_id': state_id})
                if vehicle_state_id == 19:
                    state = self.env['asset.state'].search([('id','=',vehicle_state_id)]).id
                    state_id = state + 1
                    self.env['asset.asset'].search([('type_asset','=','1'),('fleet_id.id','=',vehicle_id)])\
                        .write({'maintenance_state_id': state_id})
                if vehicle_state_id == 20:
                    state = self.env['asset.state'].search([('id','=',vehicle_state_id)]).id
                    state_id = state + 1
                    self.env['asset.asset'].search([('type_asset','=','1'),('fleet_id.id','=',vehicle_id)])\
                        .write({'maintenance_state_id': state_id})
        return super(InheritMaintenanceVehicle, self).write(context)

