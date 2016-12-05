from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
import time
import datetime
from openerp import tools


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
        cr.execute('select max(value) as value_odometer from fleet_vehicle_odometer where vehicle_id = %d' %(vehicle.id))
        odometer = cr.fetchone()[0]
        return {
            'value': {
                'odometer_unit': odometer_unit,
                'odometer': odometer,
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

    cost_id = fields.Many2one('fleet.vehicle.cost',ondelete='cascade',required=True)
    cost_type_id = fields.Many2one('fleet.service.type')
    purchaser_id = fields.Many2one('res.partner',domain="['|',('customer','=',True),('employee','=',True)]")
    inv_ref = fields.Char('Invoice Reference')
    vendor_id = fields.Many2one('res.partner')
    cost_amount = fields.Float(related='cost_id.amount',store=True)
    notes = fields.Text('notes')
    liter = fields.Float('Liter',store=True)
    price_per_liter = fields.Float('Price Per Liter',related='product_id.standard_price',store=True)
    product_id = fields.Many2one('product.product','Product',domain="[('type','=','consu'),('uom_id','=',11)]")

    _defaults = {
        'cost_subtype_id': _get_default_service_type,
        'cost_type': 'fuel',
    }

class NurseryVehicle(models.Model):

    _inherit="fleet.vehicle"
    _description = "inherit information detail to fleet management"

    def return_action_to_open_oil(self, cr, uid, ids, context=None):
        """ This opens the xml view specified in xml_id for the current vehicle """
        if context is None:
            context = {}
        if context.get('xml_id'):
            res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid ,'fleet', context['xml_id'], context=context)
            res['context'] = context
            res['context'].update({'default_vehicle_id': ids[0]})
            res['domain'] = [('vehicle_id','=', ids[0])]
            return res
        return False

    @api.multi
    @api.depends('oil_log_count')
    def _count_all_service(self):
             if self:
                 count = self.env['estate.vehicle.log.oil'].search([('vehicle_id.id','=',self.id)])
                 self.oil_log_count = len(count)

    oil_log_count = fields.Integer('Oil Log Count',compute='_count_all_service')
    other_service_log_count = fields.Integer('Other Service Log Count')
    sparepart_log_count = fields.Integer('Sparepart Log Count')
    category_unit_id = fields.Many2one('master.category.unit',domain=[('type','=','1')])
    no_vehicle=fields.Char('No Vehicle')
    odometer_unit = fields.Selection(selection_add=[('hour', 'Hour Meters')])
    # vehicle_type=fields.Selection([('1','Vehicle Internal'), ('2','Vehicle External')])
    # employee_driver_id=fields.Many2one('hr.employee')
    capacity_vehicle = fields.Integer('Capacity')
    # status_vehicle = fields.Selection([('1','Available'), ('2','Breakdown'),('3','Stand By')])




class InheritActivity(models.Model):

    _inherit = 'estate.activity'
    _description = 'inherit status'

    status = fields.Selection([('1','Available'), ('2','Breakdown'),('3','Stand By')])
    activity_vehicle_parent_id = fields.Many2one('estate.activity','Parent Activities Estate',
                                                 domain="[('activity_type','=','vehicle'),('type','=','normal')]")
    type_transport = fields.Selection([
        ('ntrip', 'Non Trip'),
        ('trip', 'Trip'),
        ], string="Type",store=True)

class InheritFuel(models.Model):

    _inherit ='fleet.vehicle.log.fuel'
    _description = 'inherit product_id in fuel'

    product_id = fields.Many2one('product.product',domain="[('type','=','consu'),('uom_id','=',11)]")


class VehicleSparepartLog(models.Model):

    _name="estate.vehicle.log.sparepart"
    _inherits = {'fleet.vehicle.cost':'cost_id'}
    _description = "Inherit view cost"

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

    def _get_default_service_type(self, cr, uid, context):
        try:
            model, model_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'fleet', 'type_service_service_8')
        except ValueError:
            model_id = False
        return model_id

    name=fields.Char()
    cost_id = fields.Many2one('fleet.vehicle.cost',ondelete='cascade',required=True)
    unit = fields.Integer('Unit Sparepart')
    product_id = fields.Many2one('product.product','Product',domain="[('type_vehicle','=',True),('type','=','product'),('uom_id','=',1)]",store=True)
    cost_amount = fields.Float(related='cost_id.amount',store=True)
    purchaser_id = fields.Many2one('res.partner',domain="['|',('customer','=',True),('employee','=',True)]")
    inv_ref = fields.Char('Invoice Reference')
    vendor_id = fields.Many2one('res.partner')
    price_per_unit = fields.Float('Price unit',readonly=1,related='product_id.standard_price',store=True)
    total_amount = fields.Float('Total Amount',compute="_compute_total_sparepart",store=True)
    notes = fields.Text('notes')

    #computed
    @api.depends('price_per_unit','unit','total_amount')
    def _compute_total_sparepart(self):
        if self.price_per_unit and self.unit:
            self.total_amount = self.price_per_unit * self.unit
        return True

    #onchange

    _defaults = {
        'cost_subtype_id': _get_default_service_type,
        'cost_type': 'services'
    }

class VehicleOtherServiceLog(models.Model):

    _name="estate.vehicle.log.otherservice"
    _inherits = {'fleet.vehicle.cost':'cost_id'}
    _description = "Inherit view cost"

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

    def _get_default_service_type(self, cr, uid, context):
        try:
            model, model_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'fleet', 'type_service_service_8')
        except ValueError:
            model_id = False
        return model_id


    name=fields.Char()
    cost_id = fields.Many2one('fleet.vehicle.cost',ondelete='cascade',required=True)
    unit = fields.Integer('Unit Service')
    product_id = fields.Many2one('product.product','Product',domain="[('type_vehicle','=',True),('type','=','service'),('uom_id','=',1)]",store=True)
    cost_amount = fields.Float(related='cost_id.amount')
    purchaser_id = fields.Many2one('res.partner',domain="['|',('customer','=',True),('employee','=',True)]")
    inv_ref = fields.Char('Invoice Reference')
    vendor_id = fields.Many2one('res.partner')
    price_per_service = fields.Float('Price Service',store=True,related='product_id.standard_price')
    total_amount = fields.Float('Total Amount',compute="_compute_total_otherservice",)
    notes = fields.Text('notes')

    #computed
    @api.depends('price_per_service','unit','total_amount')
    def _compute_total_otherservice(self):
        if self.price_per_service and self.unit:
            self.total_amount = self.price_per_service * self.unit
        return True

    _defaults = {
        'cost_subtype_id': _get_default_service_type,
        'cost_type': 'other'
    }

class InheritProduct(models.Model):

    _inherit ='product.template'

    type_vehicle = fields.Boolean('Type Vehicle',default=False)

class MasterCategoryUnit(models.Model):

    _name= 'master.category.unit'

    name=fields.Char()
    type=fields.Selection([('1','Vehicle'), ('2','Unit ALL')])

class FleetVehicleTimesheet(models.Model):



    _name = 'fleet.vehicle.timesheet'


    name = fields.Char()
    vehicle_timesheet_code = fields.Char("VTS",store=True)
    date_timesheet = fields.Date('Date',store=True)
    reject_reason =  fields.Text('Reject Reason', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Send Timesheet'),
        ('approve', 'Confirm'),
        ('done', 'Done'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled')], string="State",store=True)
    timesheet_ids = fields.One2many('inherits.fleet.vehicle.timesheet','owner_id','Timesheet Vehicle',ondelete='cascade')
    fuel_ids = fields.One2many('timesheet.fleet.vehicle.log.fuel','owner_id','Log Fuel Vehicle',ondelete='cascade')
    _defaults = {
        'state' : 'draft',
        'vehicle_timesheet_code':lambda obj, cr, uid, context: obj.pool.get('ir.sequence').next_by_code(cr, uid, 'fleet.vehicle.timesheet'),
    }

    #sequence
    def create(self, cr, uid,vals, context=None):
        for item in vals['timesheet_ids']:
            item[2]['date_activity_transport'] = vals['date_timesheet']
            item[2]['state'] = 'draft'
        for item2 in vals['fuel_ids']:
            item2[2]['date']=vals['date_timesheet']
        res=super(FleetVehicleTimesheet, self).create(cr, uid,vals)
        return res

    @api.multi
    def write(self,context):
        super(FleetVehicleTimesheet, self).write(context)
        self.env['estate.timesheet.activity.transport'].search([('owner_id','=',self.id)]).write({'state': 'draft'})
        self.do_write_vehicle_date()
        return True

    @api.multi
    def unlink(self):
        self.env['estate.timesheet.activity.transport'].search([('owner_id','=',self.id)]).unlink()
        self.env['timesheet.fleet.vehicle.log.fuel'].search([('owner_id','=',self.id)]).unlink()
        return super(FleetVehicleTimesheet, self).unlink()

    @api.multi
    def action_send(self,):
        self.write({'state': 'confirm'})
        self.env['estate.timesheet.activity.transport'].search([('owner_id','=',self.id)]).write({'state': 'confirmed'})
        return True

    @api.multi
    def action_confirm(self,):
        """ Confirms Timesheet request.
        @return: timesheet all.
        """
        name = self.name
        self.write({'name':"Vehicle Timesheet %s " %(name)})
        self.write({'state': 'done'})
        self.do_create_vehicle_odometer_log()
        self.do_create_vehicle_log_fuel()
        self.env['estate.timesheet.activity.transport'].search([('owner_id','=',self.id)]).write({'state': 'done'})
        return True

    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done', 'date_timesheet': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    @api.multi
    def action_reject(self,):
        self.write({'state': 'reject', 'date_timesheet': self.date_timesheet})
        self.env['estate.timesheet.activity.transport'].search([('owner_id','=',self.id)]).write({'state': 'reject'})
        self.do_write_vehicle_date()
        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel', 'date_timesheet': self.date_timesheet})
        self.env['estate.timesheet.activity.transport'].search([('owner_id','=',self.id)]).write({'state': 'cancel'})
        return True

    @api.multi
    def do_write_vehicle_date(self):
        #Update date in inherit timesheet.
        date = False
        fleet = self.env['fleet.vehicle.timesheet'].search([('id','=',self.id)],order='id desc',limit=1)
        for date in fleet:
            date_data = {
                'date_activity_transport': date.date_timesheet,
            }
            self.env['inherits.fleet.vehicle.timesheet'].search([('owner_id','=',fleet.id)]).write(date_data)
        return True


    @api.multi
    def do_create_vehicle_odometer_log(self):
        #create odometer LOG from inherits.fleet.vehicle.timesheet
        odometer = False
        for odometer in self.env['inherits.fleet.vehicle.timesheet'].search([('owner_id','=',self.id)]):
            odometer_data = {
                'name':'Odometer',
                'date': self.date_timesheet,
                'vehicle_id': odometer.vehicle_id.id,
                'value': odometer.end_km,
            }
            self.env['fleet.vehicle.odometer'].create(odometer_data)
        return True

    @api.multi
    def do_create_vehicle_log_fuel(self):
        #create vehicle Log Fuel from timesheet.fleet.vehicle.log.fuel
        fuel = False
        for fuel in self.env['timesheet.fleet.vehicle.log.fuel'].search([('owner_id','=',self.id)]):
            fuel_data = {
                'date': self.date_timesheet,
                'vehicle_id': fuel.vehicle_id.id,
                'liter' : fuel.liter,
                'price_per_liter' : fuel.price_per_liter,
                'purchaser_id' : fuel.purchaser_id.id,
                'vendor_id' : fuel.vendor_id.id,
                'notes' : fuel.notes,
                'amount' : fuel.amount,
                'odometer': fuel.odometer,
                'odometer_unit':fuel.odometer_unit,
                'product_id':fuel.product_id.id
            }
            self.env['fleet.vehicle.log.fuel'].create(fuel_data)
        return True


    @api.multi
    @api.constrains('date_timesheet')
    def _constraint_date_timesheet(self):
        tempdate = []
        for item in self:
            date = item.env['fleet.vehicle.timesheet'].search([('state','=','done')])
            for date in date:
                tempdate.append(date.date_timesheet)
            if item.date_timesheet in tempdate:
                error_msg = "Date Timesheet %s Not Use More Than One" %item.date_timesheet
                raise exceptions.ValidationError(error_msg)

    @api.multi
    @api.constrains('timesheet_ids','fuel_ids')
    def _constraint_vehicle_id_notnull(self):

        if self.timesheet_ids:
            for vehicle in self.timesheet_ids:
                if not vehicle.vehicle_id.id:
                    error_msg = "Vehicle Field in Timesheet Tab Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                    return False
            return True

    @api.multi
    @api.constrains('fuel_ids')
    def _constrat_fuel_ids(self):
        if self.fuel_ids:
            for vehicle in self.fuel_ids:
                if not vehicle.vehicle_id.id:
                    error_msg = "Vehicle Field in Fuel Tab Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                    return False
            return True


class FleetVehicleTimesheetInherits(models.Model):

    _name = 'inherits.fleet.vehicle.timesheet'
    _inherits = {'estate.timesheet.activity.transport':'timesheet_id'}

    timesheet_id = fields.Many2one('estate.timesheet.activity.transport',ondelete='cascade',required=True)
    total_distance = fields.Float(digits=(2,2),compute='_compute_total_distance',store=True)
    distance_location = fields.Float('Distance Location',store=True,compute='_onchange_distance_location')
    total_time = fields.Float(digits=(2,2),compute='_compute_total_time')
    type_transport = fields.Selection([
        ('ntrip', 'Non Trip'),
        ('trip', 'Trip'),
        ], string="Type",store=True,compute='change_type_transport')
    comment = fields.Text()


    @api.multi
    @api.onchange('dc_type')
    def _onchange_dc_type(self):
        if self:
            self.dc_type = 5

    @api.multi
    def unlink(self):
        self.timesheet_id.unlink()
        return super(FleetVehicleTimesheetInherits, self).unlink()

    #onchange ALL
    @api.multi
    @api.onchange('start_location')
    def _onchange_path_end_location(self):
        #use to onchange domain end_location same as master location path
        if self:
            if self.start_location:
                arrEndlocation=[]
                arrStartlocation = []
                temp=[]
                endlocation=self.env['path.location'].search([('start_location.id','=',self.start_location.id)])
                allLocation=self.env['estate.block.template'].search([])
                for record in allLocation:
                    temp.append(record.id)
                for record in endlocation:
                        arrStartlocation.append(record.start_location.id)
                if self.start_location.id in arrStartlocation:
                    for record in endlocation:
                        arrEndlocation.append(record.end_location.id)
                    return {
                    'domain':{
                        'end_location':[('id','in',arrEndlocation)]
                    }
                }
                elif self.start_location.id not in arrStartlocation:
                    return {
                    'domain':{
                        'end_location':[('id','in',temp)]
                         }
                    }
                else:
                    return {
                    'domain':{
                        'end_location':[('id','in',temp)]
                         }
                    }

    @api.multi
    @api.onchange('type_transport')
    def _onchange_unit(self):
        if self.type_transport =='trip':
            self.unit = 1
        elif self.type_transport == 'ntrip':
            self.unit = 0

    @api.multi
    @api.depends('activity_id')
    def change_type_transport(self):
        for item in self:
            if item.activity_id.type_transport:
                item.type_transport = item.activity_id.type_transport
            else :
                item.type_transport = 'trip'

    @api.multi
    @api.depends('distance_location','end_location','start_location')
    def _onchange_distance_location(self):
        #to change distance location same master path location
        for item in self:
            if item.start_location and item.end_location:
                try:
                    arrDistance = 0
                    distancelocation = item.env['path.location'].search([
                        ('start_location.id','=',item.start_location.id),('end_location.id','=',item.end_location.id)])
                    for c in distancelocation:
                        arrDistance += c.distance_location
                    item.distance_location = arrDistance
                except:
                    item.distance_location = 0
        return True

    @api.multi
    @api.onchange('employee_id')
    def _onchange_driver(self):
        arrDriver = []
        if self:
            hrjob = self.env['hr.job'].search([('name','in',['sopir','Sopir','Driver','driver'])],limit = 1).id
            driver = self.env['hr.employee'].search([('job_id.id','=',hrjob)])
            for d in driver:
                arrDriver.append(d.id)
        return {
                'domain':{
                    'employee_id':[('id','in',arrDriver)]
                }
        }

    @api.multi
    @api.onchange('activity_id')
    def _onchange_uom(self):
        #onchange UOM in timesheet Vehicle
        if self.activity_id:
            self.uom_id = self.activity_id.uom_id

    #todo get odometer
    # @api.multi
    # @api.onchange('vehicle_id')
    # def _onchange_end_km(self):
    #     #onchange start km on fleet vehicle timesheet
    #         if self.vehicle_id:
    #             end_km= self.env['estate.timesheet.activity.transport'].search([('owner_id','=',self.owner_id),
    #                                                                              ('vehicle_id','=',self.vehicle_id.id)
    #                                                                              ],order='id desc', limit=1).end_km
    #             self.start_km = end_km


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
                vehicle=self.env['fleet.vehicle'].search([('maintenance_state_id.id','=',21)])
                for v in vehicle:
                    arrVehicletransport.append(v.id)
                return {
                    'domain':{
                        'vehicle_id':[('id','in',arrVehicletransport)]
                        }
                    }


    #Computed ALL
    @api.multi
    @api.depends('start_time','end_time','total_time')
    def _compute_total_time(self):
        self.ensure_one()
        #to compute total_time
        if self:
            if self.start_time and self.end_time:
                calculate_endtime = round(self.end_time%1*0.6,2)+(self.end_time-self.end_time%1)
                calculate_starttime = round(self.start_time%1*0.6,2)+(self.start_time-self.start_time%1)
                self.total_time =calculate_endtime-calculate_starttime
                if self.total_time < 0 :
                    self.total_time = 0
        return True

    @api.multi
    @api.depends('start_km','end_km')
    def _compute_total_distance(self):
        #to Compute total Distance
        for item in self:
            if item.end_km and item.start_km:
                item.total_distance = item.end_km - item.start_km



    #Constraint ALL




    @api.multi
    @api.constrains('start_km','end_km')
    def _constraint_startkm_endkm(self):

        for item in self:
            if item.end_km < item.start_km:
                error_msg="End KM  %s is set more less than Start KM %s " %(self.end_km,self.start_km)
                raise exceptions.ValidationError(error_msg)
            return True

    @api.multi
    @api.constrains('start_time','end_time')
    def _constraint_starttime_endtime(self):
        Max = float(24.0)
        Min = float(0.0)
        if self:
            if self.start_time < Min:
                error_msg = "Start Time Not More Less Than 00:00"
                raise exceptions.ValidationError(error_msg)
            if self.end_time < Min:
                error_msg = "End Time Not More Less Than 00:00"
                raise exceptions.ValidationError(error_msg)
            if self.start_time >  Max:
                error_msg = "Start Time Not More Than 24:00"
                raise exceptions.ValidationError(error_msg)
            if self.end_time > Max :
                error_msg = "End Time Not More Than 24:00"
                raise exceptions.ValidationError(error_msg)
            if self.end_time < self.start_time:
                calculate_endtime = round(self.end_time%1*0.6,2)+(self.end_time-self.end_time%1)
                calculate_starttime = round(self.start_time%1*0.6,2)+(self.start_time-self.start_time%1)
                error_msg="End Time  %s is set more less than Start Time %s " %(calculate_endtime,calculate_starttime)
                raise exceptions.ValidationError(error_msg)
            return True

class InheritFleetVehicleFuel(models.Model):

    _name = 'timesheet.fleet.vehicle.log.fuel'
    _description = "Fuel Log"

    def on_change_vehicle(self, cr, uid, ids, vehicle_id, context=None):
        #get last odometer from log odometer
        if not vehicle_id:
            return {}
        vehicle = self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_id, context=context)
        last_odometer = self.pool.get('fleet.vehicle.odometer').search(cr, uid,([('vehicle_id.id','=',vehicle.id)]),context=context,order='id desc',limit=1)
        odometer = self.pool.get('fleet.vehicle.odometer').browse(cr, uid, last_odometer, context=context)
        odometer_value = odometer.value
        odometer_unit = vehicle.odometer_unit
        driver = vehicle.driver_id.id
        return {
            'value': {
                'odometer_unit': odometer_unit,
                'purchaser_id': driver,
                'odometer': odometer_value,
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


    fuel_id = fields.Many2one('fleet.vehicle.log.fuel','Fuel ID')
    owner_id = fields.Integer('Owner ID')
    vehicle_id = fields.Many2one('fleet.vehicle','Vehicle')
    liter =  fields.Float('Liter')
    price_per_liter = fields.Float('Price Per Liter')
    purchaser_id =  fields.Many2one('res.partner', 'Purchaser', domain="['|',('customer','=',True),('employee','=',True)]")
    vendor_id = fields.Many2one('res.partner', 'Vendor', domain="[('supplier','=',True)]")
    notes = fields.Text('Notes')
    amount = fields.Float('Amount')
    odometer = fields.Float('Odometer')
    odometer_unit = fields.Selection('Odometer Unit' , related='vehicle_id.odometer_unit')
    date = fields.Date('Date')
    product_id = fields.Many2one('product.product','Product',domain="[('type','=','consu'),('uom_id','=',11)]")











