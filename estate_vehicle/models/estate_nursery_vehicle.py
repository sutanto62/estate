from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar




class NurseryVehicle(models.Model):


    _inherit="fleet.vehicle"
    _description = "inherit information detail to fleet management"

    @api.model
    def _count_oil(self):
        if self.oil_log_count:
            return {
                vehicle_id:
                    {
                     'oil_log_count': self.env['estate.vehicle.log.oil'].search_count([('vehicle_id', '=', vehicle_id)])
                    }
                for vehicle_id in self.ids
            }

    oil_log_count = fields.Integer('Oil Log Count',compute='_count_oil')
    no_vehicle=fields.Char('No Vehicle')
    vehicle_type=fields.Selection([('1','Vehicle Internal'), ('2','Vehicle External')])
    employee_driver_id=fields.Many2one('hr.employee')
    capacity_vehicle = fields.Integer('Capacity')
    status_vehicle = fields.Selection([('1','Available'), ('2','Breakdown')])

class VehicleOilLog(models.Model):

    _name="estate.vehicle.log.oil"
    _inherits = {'fleet.vehicle.cost':'cost_id'}
    _description = "Inherit view fuel log"


    def on_change_vehicle(self, cr, uid, ids, vehicle_id, context=None):
        if not vehicle_id:
            return {}
        vehicle = self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_id, context=context)
        odometer_unit = vehicle.odometer_unit
        driver = vehicle.driver_id.id
        return {
            'value': {
                'odometer_unit': odometer_unit,
                'purchaser_id': driver,
            }
        }

    def on_change_liter(self, cr, uid, ids, liter, price_per_liter, amount, context=None):
        #need to cast in float because the value receveid from web client maybe an integer (Javascript and JSON do not
        #make any difference between 3.0 and 3). This cause a problem if you encode, for example, 2 liters at 1.5 per
        #liter => total is computed as 3.0, then trigger an onchange that recomputes price_per_liter as 3/2=1 (instead
        #of 3.0/2=1.5)
        #If there is no change in the result, we return an empty dict to prevent an infinite loop due to the 3 intertwine
        #onchange. And in order to verify that there is no change in the result, we have to limit the precision of the
        #computation to 2 decimal
        liter = float(liter)
        price_per_liter = float(price_per_liter)
        amount = float(amount)
        if liter > 0 and price_per_liter > 0 and round(liter*price_per_liter,2) != amount:
            return {'value' : {'amount' : round(liter * price_per_liter,2),}}
        elif amount > 0 and liter > 0 and round(amount/liter,2) != price_per_liter:
            return {'value' : {'price_per_liter' : round(amount / liter,2),}}
        elif amount > 0 and price_per_liter > 0 and round(amount/price_per_liter,2) != liter:
            return {'value' : {'liter' : round(amount / price_per_liter,2),}}
        else :
            return {}

    def on_change_price_per_liter(self, cr, uid, ids, liter, price_per_liter, amount, context=None):
        #need to cast in float because the value receveid from web client maybe an integer (Javascript and JSON do not
        #make any difference between 3.0 and 3). This cause a problem if you encode, for example, 2 liters at 1.5 per
        #liter => total is computed as 3.0, then trigger an onchange that recomputes price_per_liter as 3/2=1 (instead
        #of 3.0/2=1.5)
        #If there is no change in the result, we return an empty dict to prevent an infinite loop due to the 3 intertwine
        #onchange. And in order to verify that there is no change in the result, we have to limit the precision of the
        #computation to 2 decimal
        liter = float(liter)
        price_per_liter = float(price_per_liter)
        amount = float(amount)
        if liter > 0 and price_per_liter > 0 and round(liter*price_per_liter,2) != amount:
            return {'value' : {'amount' : round(liter * price_per_liter,2),}}
        elif amount > 0 and price_per_liter > 0 and round(amount/price_per_liter,2) != liter:
            return {'value' : {'liter' : round(amount / price_per_liter,2),}}
        elif amount > 0 and liter > 0 and round(amount/liter,2) != price_per_liter:
            return {'value' : {'price_per_liter' : round(amount / liter,2),}}
        else :
            return {}

    def on_change_amount(self, cr, uid, ids, liter, price_per_liter, amount, context=None):
        #need to cast in float because the value receveid from web client maybe an integer (Javascript and JSON do not
        #make any difference between 3.0 and 3). This cause a problem if you encode, for example, 2 liters at 1.5 per
        #liter => total is computed as 3.0, then trigger an onchange that recomputes price_per_liter as 3/2=1 (instead
        #of 3.0/2=1.5)
        #If there is no change in the result, we return an empty dict to prevent an infinite loop due to the 3 intertwine
        #onchange. And in order to verify that there is no change in the result, we have to limit the precision of the
        #computation to 2 decimal
        liter = float(liter)
        price_per_liter = float(price_per_liter)
        amount = float(amount)
        if amount > 0 and liter > 0 and round(amount/liter,2) != price_per_liter:
            return {'value': {'price_per_liter': round(amount / liter,2),}}
        elif amount > 0 and price_per_liter > 0 and round(amount/price_per_liter,2) != liter:
            return {'value': {'liter': round(amount / price_per_liter,2),}}
        elif liter > 0 and price_per_liter > 0 and round(liter*price_per_liter,2) != amount:
            return {'value': {'amount': round(liter * price_per_liter,2),}}
        else :
            return {}

    def _get_default_service_type(self, cr, uid, context):
        try:
            model, model_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'fleet', 'type_service_refueling')
        except ValueError:
            model_id = False
        return model_id

    name=fields.Char()
    cost_id = fields.Many2one('fleet.vehicle.cost',ondelete='cascade')
    cost_type_id = fields.Many2one('fleet.service.type')
    purchaser_id = fields.Many2one('res.partner',domain="['|',('customer','=',True),('employee','=',True)]")
    inv_ref = fields.Char('Invoice Reference')
    vendor_id = fields.Many2one('res.partner')
    cost_amount = fields.Float(related='cost_id.amount')
    notes = fields.Text('notes')
    liter = fields.Float('Liter')
    price_per_liter = fields.Float('Price Per Liter')
    product_id = fields.Many2one('product.product','Product',domain="[('type','=','consu'),('uom_id','=',11)]")













