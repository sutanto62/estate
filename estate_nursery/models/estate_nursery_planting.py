from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar

class Planting(models.Model):
    #seed planting

    def return_action_to_open(self, cr, uid, ids, context=None):
        """ This opens the xml view specified in xml_id for the current Batch """
        if context is None:
            context = {}
        if context.get('xml_id'):
            res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid ,'estate_nursery', context['xml_id'], context=context)
            res['context'] = context
            res['context'].update({'default_seeddo_id': ids[0]})
            res['domain'] = [('seeddo_id','=', ids[0])]
            return res
        return False

    _name = "estate.nursery.seeddo"
    _description = "Seed Delivery Order"
    _inherit = ['mail.thread']

    name=fields.Char("Planting Code")
    seeddo_code=fields.Char("Seed Delivery Code")
    partner_id=fields.Many2one('res.partner')
    dotransportir_ids = fields.One2many('estate.nursery.dotransportir','seeddo_id','InformationTransportir')
    activityline_ids=fields.One2many('estate.nursery.activityline','seeddo_id','Information Activity Transportir')
    request_ids = fields.One2many('estate.nursery.request','seeddo_id',"Request Ids",help="Define Many Bpb")
    # timesheet_ids = fields.One2many('estate.timesheet.activity.transport','owner_id','Timesheet ids')
    return_ids = fields.One2many('estate.nursery.returnseed','seeddo_id',"Returns Ids",help="Define Many Return Bpb")
    picking_id = fields.Many2one('stock.picking', "Picking", readonly=True)
    date_request = fields.Date('Date Seed Delivery Order',required=True)
    total_qty_pokok= fields.Integer("Total Pokok",compute="compute_total_qty_pokok",track_visibility='onchange')
    expense = fields.Integer("Amount Expense",compute="_amount_all",track_visibility='onchange')
    amount_total = fields.Integer('Total Amount Transportir')
    comment=fields.Text("Additional Information")
    state=fields.Selection([('draft','Draft'),('confirmed','Confirm'),
                            ('open2','Open Pending'),('pending2','Pending'),
            ('pending','Pending'),('open','Open Pending'),
            ('validate1','First Approval'),('validate2','Second Approval'),
                            ('done','Ordered'),('return','Return Seed'),
                            ('validate3','Return Approval'),
                            ('done2','Done')])

    @api.cr_uid_ids_context
    def do_enter_transfer_details(self, cr, uid, seeddo, context=None):
        if not context:
            context = {}

        context.update({
            'active_model': self._name,
            'active_ids': seeddo,
            'active_id': len(seeddo) and seeddo[0] or False
        })

        created_id = self.pool['estate.nursery.transfer'].create(cr, uid, {'seeddo_id': len(seeddo) and seeddo[0] or False}, context)
        return self.pool['estate.nursery.transfer'].wizard_view(cr, uid, created_id, context)

    #sequence
    def create(self, cr, uid, vals, context=None):
        vals['seeddo_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.seeddo')
        res=super(Planting, self).create(cr, uid, vals)
        return res

    #state
    @api.one
    def action_draft(self):
        """Set planting State to Draft."""
        self.state = 'draft'

    @api.one
    def action_confirmed(self):
        """Set Planting state to Confirmed."""
        countLineActivity = 0
        countLineVehicle = 0
        countLineRequest = 0
        for itemline in self:
            countLineRequest += len(itemline.request_ids)
            countLineActivity += len(itemline.activityline_ids)
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
        serial = self.env['estate.nursery.request'].search_count([]) + 1
        self.write({'name':"SPB %d" %serial})
        self.state = 'confirmed'

    @api.one
    def action_approved1(self):
        """Approved planting is validate 1."""
        self.state = 'validate1'

    @api.one
    def action_approved2(self):
        """Approved Planting is validate 2."""
        self.state = 'validate2'

    @api.one
    def action_open_pending(self):
        """Set Planting State to open."""
        self.state = 'open'
    @api.one
    def action_open_pending2(self):
        """Set Planting State to open."""
        self.state = 'open2'

    @api.one
    def action_pending(self):
        """Set Selection State to pending."""
        self.state = 'pending'
    @api.one
    def action_pending2(self):
        """Set Selection State to pending."""
        self.state = 'pending2'


    @api.one
    def action_approved(self):
        """Approved Planting is done."""
        self.state = 'done'


    #Compute Amount ALL
    @api.one
    @api.depends('activityline_ids','expense')
    def _amount_all(self):
        if self.activityline_ids:
            for price in self.activityline_ids:
                self.expense += price.result_price
        return True

    #compute Qty Planted transplanting
    @api.one
    @api.depends('return_ids','request_ids')
    def compute_total_qty_pokok(self):
        total_request = 0
        total_return = 0
        if self.state == "done":
            if self.request_ids:
                for qty in self.request_ids:
                    total_request += qty.total_qty_pokok
            if self.return_ids and  self.request_ids:
                for qty in self.return_ids:
                    total_return += qty.total_qty_return
            try:
                self.total_qty_pokok = total_request-total_return
            except:
                self.qty_planted = total_request-0
            # self.total_qty_pokok = total_request-total_return
        return True

    #Onchange FOR ALL
    @api.onchange('amount_total','expense')
    def change_total(self):
        self.amount_total = self.expense
        self.write({'amount_total':self.amount_total})

    # Constraint For ALL

    @api.multi
    @api.constrains('request_ids','return_ids')
    def _constraints_request_return_seed(self):
        #Constraint Return line must be same with line in bpb
        if self.return_ids:
            countLine = 0
            countLineReturn = 0
            for r in self:
                countLine += len(r.request_ids)
                countLineReturn += len(r.return_ids)
            if countLineReturn > countLine:
                error_msg = "Tab Return Seed Must be match with line in BPB"
                raise exceptions.ValidationError(error_msg)

    @api.multi
    @api.constrains('return_ids','request_ids','dotransportir_ids','activityline_ids')
    def _constraints_line_mustbe_filled(self):
        #Constraint Line return , request , transportir, activityin planting must be filled
            countRequest = 0
            countDotranport = 0
            countActivity = 0
            for item in self:
                countActivity += len(item.activityline_ids)
                countDotranport += len(item.dotransportir_ids)
                countRequest += len(item.request_ids)
            if countRequest == 0 :
                error_msg = "Tab Request Must be filled"
                raise exceptions.ValidationError(error_msg)
            if countActivity == 0 :
                error_msg = "Tab Transportir Activity Must be filled"
                raise exceptions.ValidationError(error_msg)
            if countDotranport == 0 :
                error_msg = "Tab Detail Transportir Must be filled"
                raise exceptions.ValidationError(error_msg)


class TransportirDetail(models.Model):

    _name = 'estate.nursery.dotransportir'

    seeddo_id = fields.Many2one('estate.nursery.seeddo')
    estate_vehicle_id= fields.Many2one('fleet.vehicle','Estate Vehicle',track_visibility='onchange')
    # driver_internal_id=fields.Char(related='estate_vehicle_id.employee_driver_id',readonly=True,track_visibility='onchange')
    driver_estate_id = fields.Many2one(related='estate_vehicle_id.driver_id',readonly=True,track_visibility='onchange')
    driver=fields.Char('Driver')
    capacity = fields.Integer('Capacity')
    vehicle_type = fields.Selection([('1','Vehicle Internal'), ('2','Vehicle External')])
    no_vehicle = fields.Char('No Vehicle Transportir')

    #onchange Driver Transportir external and internal
    @api.one
    @api.onchange('driver_internal_id','vehicle_type','driver_estate_id','estate_vehicle_id','driver')
    def onchange_driver(self):
        type = self.estate_vehicle_id.vehicle_type

        if self.estate_vehicle_id:
            # if type == '1':
            #     # self.driver=self.driver_internal_id.name
            if type == '2':
                self.driver=self.driver_estate_id.name
            else :
                self.driver=self.driver_estate_id.name
        return True

    @api.one
    @api.onchange('estate_vehicle_id','capacity')
    def _onchange_capacity(self):
        if self.estate_vehicle_id:
            self.capacity = self.estate_vehicle_id.capacity_vehicle
        return True

    #onchange detail vehicle
    @api.one
    @api.onchange('estate_vehicle_id','vehicle_type','no_vehicle')
    def onchange_vehicle_status(self):
        if self.estate_vehicle_id:
            self.vehicle_type = self.estate_vehicle_id.vehicle_type
            self.no_vehicle = self.estate_vehicle_id.no_vehicle
        return True

    @api.multi
    @api.onchange('estate_vehicle_id')
    def _onchange_vechicle(self):
        # on change vehicle id where status available
        arrVehicle=[]
        if self:
            vehicle=self.env['fleet.vehicle'].search([('maintenance_state_id.id','=',21)])
            for v in vehicle:
                    arrVehicle.append(v.id)
        return {
                'domain':{
                    'estate_vehicle_id':[('id','in',arrVehicle)]
                }
        }

class ActivityLine(models.Model):

    _name = "estate.nursery.activityline"

    name=fields.Char()
    seeddo_id=fields.Many2one('estate.nursery.seeddo')
    activity_id=fields.Many2one('estate.activity')
    product_type_id=fields.Many2one('product.uom',readonly=True)
    price=fields.Float("Price/Quantity" , readonly=True)
    qty_product=fields.Integer("Quantity Product Transfer")
    transportactivity_expense_id = fields.Many2one('account.account', "Expense Account",
                                         help="This account will be used for invoices to value expenses")
    result_price=fields.Float("Quantity Result",compute="calculate_price")

    @api.one
    def change_name(self):
        serial=self.env['estate.nursery.activityline'].search_count([])+ 1
        self.write({'name':"Activity %d" % serial})

    @api.one
    @api.onchange('product_type_id','activity_id')
    def change_product_type_id(self):
        self.product_type_id = self.activity_id.uom_id.id


    @api.one
    @api.onchange('activity_id','price')
    def change_price(self):
        self.price = self.activity_id.standard_price
        self.write({'price' : self.price})

    @api.one
    @api.depends('qty_product','price')
    def calculate_price(self):
        price=float(self.price)
        product=int(self.qty_product)
        if self.qty_product and self.price:
            result=price*product
            self.result_price=result
        return True


