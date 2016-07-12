from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal



class ViewVehiclePreventiveOdometer(models.Model):

    _name = "vehicle.preventive.odometer"
    _description = "Function to Vehicle Preventive Odometer "
    _auto = False

    def init(self, cr):
        cr.execute("""CREATE OR REPLACE VIEW vehicle_preventive_odometer AS
             SELECT a.fleet_id,
                a.asset_id,
                a.odometer,
                b.odometer_current,
                count_multiply_odometer(a.odometer::integer, b.odometer_current::integer) AS count_multiply,
                count_multiply_odometer(a.odometer::integer, b.odometer_current::integer) * a.odometer::integer % b.odometer_current::integer AS odometer_remain,
                a.odometer * 0.01::double precision AS odometer_threshold
               FROM ( SELECT m.id,
                        a_1.fleet_id,
                        m.odometer,
                        m.asset_id
                       FROM estate_master_workshop_shedule_plan m
                         JOIN asset_asset a_1 ON m.asset_id = a_1.id
                      WHERE m.type::text <> 'view'::text) a
                 LEFT JOIN ( SELECT fleet_vehicle_odometer.vehicle_id,
                        max(fleet_vehicle_odometer.value) AS odometer_current
                       FROM fleet_vehicle_odometer
                      GROUP BY fleet_vehicle_odometer.vehicle_id) b ON a.fleet_id = b.vehicle_id;
                   """)
