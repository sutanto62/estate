from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar

class Planting(models.Model):
    #seed planting
    _name = "estate.nursery.seeddo"
    _description = "Seed Delivery Order"
    # _inherits = {'estate.nursery.batch' : 'batch_id'}
    _inherit = ['mail.thread']

    name=fields.Char("Planting Code")
    seeddo_code=fields.Char("Seed Delivery Code")
    partner_id=fields.Many2one('res.partner')
    dotransportir_ids = fields.One2many('estate.nursery.dotransportir','seeddo_id','InformationTransportir')
    activityline_ids=fields.One2many('estate.nursery.activityline','seeddo_id','Information Activity Transportir')
    batch_planted_ids= fields.One2many('estate.batch.parameter','seeddo_id', "Batch Parameter",
                                          help="Define batch parameter")
    picking_id = fields.Many2one('stock.picking', "Picking", readonly=True)
    date_request = fields.Date('Date Seed Delivery Order',required=True)
    total_qty_pokok= fields.Integer("Total Pokok",compute="compute_total_qty_pokok",track_visibility='onchange')
    expense = fields.Integer("Amount Expense",compute="_amount_all",track_visibility='onchange')
    amount_total = fields.Integer('Total Amount Transportir')
    comment=fields.Text("Additional Information")
    state=fields.Selection([('draft','Draft'),('confirmed','Confirm'),
            ('validate1','First Approval'),('validate2','Second Approval'),('done','Ordered')])

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
    def action_approved(self):
        """Approved Planting is done."""
        # self.action_receive()
        self.state = 'done'

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

    # @api.one
    # def action_receive(self):
    #
    # @api.one
    # def action_receive(self):
    #     qty_req = self.total_qty_pokok
    #     requestlineids = self.requestline_ids
    #
    #     for item in requestlineids:
    #         qty_req += item.qty_request
    #     self.write({'total_qty_pokok': self.total_qty_pokok})
    #
    #     return True

    # #count selection
    # @api.one
    # @api.depends('request_ids')
    # def _get_request_count(self):
    #     for r in self:
    #         r.request_count = len(r.request_ids)

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
    @api.depends('batch_planted_ids')
    def compute_total_qty_pokok(self):
        if self.batch_planted_ids:
            for qty in self.batch_planted_ids:
                self.total_qty_pokok += qty.total_qty_pokok
                print self.total_qty_pokok

    #Onchange FOR ALL
    @api.onchange('amount_total','expense')
    def change_total(self):
        self.amount_total = self.expense
        self.write({'amount_total':self.amount_total})

    #Constraint For ALL
    #Constraint bpb choose not more than 1
    @api.one
    @api.constrains('batch_planted_ids')
    def _constrains_parameter_bpb(self):
        if self.batch_planted_ids:
            temp={}
            for bpb in self.batch_planted_ids:
                bpb_value_name = bpb.bpb_id.name
                if bpb_value_name in temp.values():
                    error_msg = "Request Seed \"%s\" is set more than once " % bpb_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[bpb.id] = bpb_value_name
            return temp

class TransportirDetail(models.Model):

    _name = 'estate.nursery.dotransportir'

    seeddo_id = fields.Many2one('estate.nursery.seeddo')
    estate_vehicle_id= fields.Many2one('fleet.vehicle','Estate Vehicle',track_visibility='onchange')
    driver_internal_id=fields.Many2one(related='estate_vehicle_id.employee_driver_id',readonly=True,track_visibility='onchange')
    driver_estate_id = fields.Many2one(related='estate_vehicle_id.driver_id',readonly=True,track_visibility='onchange')
    driver=fields.Char('Driver')
    vehicle_type = fields.Selection([('1','Vehicle Internal'), ('2','Vehicle External')])
    no_vehicle = fields.Char('No Vehicle Transportir')

    #onchange Driver Transportir external and internal
    @api.one
    @api.onchange('driver_internal_id','vehicle_type','driver_estate_id','estate_vehicle_id','driver')
    def onchange_driver(self):
        type = self.estate_vehicle_id.vehicle_type

        if self.estate_vehicle_id:
            if type == '1':
                self.driver=self.driver_internal_id.name
            elif type == '2':
                self.driver=self.driver_estate_id.name
            else :
                self.driver=self.driver_estate_id.name
        return True

    #onchange detail vehicle
    @api.one
    @api.onchange('estate_vehicle_id','vehicle_type','no_vehicle')
    def onchange_vehicle_status(self):
        if self.estate_vehicle_id:
            self.vehicle_type = self.estate_vehicle_id.vehicle_type
            self.no_vehicle = self.estate_vehicle_id.no_vehicle


class ActivityLine(models.Model):
    _name = "estate.nursery.activityline"
    _inherits = {'estate.activity' : 'activity_id'}

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


class BatchParameter(models.Model):
    """Parameter of Batch.
    """
    _name = 'estate.batch.parameter'
    _inherit=['mail.thread']

    bpb_id=fields.Many2one('estate.nursery.request','BPB Form')
    variety_id=fields.Many2one('estate.nursery.variety',related='bpb_id.variety_id',readonly=True)
    total_qty_pokok = fields.Integer('Qty Request',track_visibility='onchange',readonly=True)
    batch_id = fields.Many2one('estate.nursery.batch', "Nursery Batch",
                               domain=[('selection_count','>=',6),('qty_planted','>',0),('age_seed_range','>=', 6)],
                               track_visibility='onchange')
    seeddo_id=fields.Many2one('estate.nursery.seeddo')
    from_location_id = fields.Many2many('estate.block.template','batch_rel_loc','inherit_location_id','val_id', "From Location",
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),
                                                  ('stage_id','=',4),
                                                  ('scrap_location', '=', False),
                                                  ])
    parameter_value_id = fields.Many2one('estate.bpb.value', "Value",
                                         domain="[('parameter_id', '=', parameter_id)]",
                                         ondelete='restrict')

    #onchange total qty pokok
    @api.one
    @api.onchange('bpb_id','total_qty_pokok')
    def onchange_total_qty_pokok(self):
        self.total_qty_pokok = self.bpb_id.total_qty_pokok
        self.write({'total_qty_pokok' : self.total_qty_pokok})


