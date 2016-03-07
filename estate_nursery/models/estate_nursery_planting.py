from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar

class Planting(models.Model):
    #seed planting
    _name = "estate.nursery.seeddo"
    _description = "Seed Delivery Order"
    _inherit = ['mail.thread']

    name=fields.Char("Planting Code")
    planting_code=fields.Char("Planting Code")
    estate_vehicle_id= fields.Many2one('fleet.vehicle','Estate Vehicle',track_visibility='onchange')
    driver_estate_id = fields.Many2one(related="estate_vehicle_id.driver_id",readonly=True,track_visibility='onchange')
    vehicle_type = fields.Selection([('1','Vehicle Internal'), ('2','Vehicle External')],
                                    related="estate_vehicle_id.vehicle_type")
    no_vehicle = fields.Char(related="estate_vehicle_id.no_vehicle")
    activityline_ids=fields.One2many('estate.nursery.activityline','seeddo_id','Information Activity Transportir')
    product_id = fields.Many2one('product.product', "Product", related="lot_id.product_id")
    picking_id = fields.Many2one('stock.picking', "Picking", readonly=True)
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)])
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety", required=True, ondelete="restrict")
    seed_location_id = fields.Many2one('estate.block.template', ("Seed Location"),track_visibility='onchange',
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),
                                                  ('scrap_location', '=', False),
                                                  ])
    batch_planted_ids= fields.One2many('estate.batch.parameter','batch_id', "Batch Parameter",
                                          help="Define batch parameter")
    date_request = fields.Date('Date Seed Delivery Order',required=True)
    total_qty_pokok= fields.Date("Total Pokok",track_visibility='onchange')
    expense = fields.Integer("Amount Expense",compute="_amount_all",track_visibility='onchange')
    amount_total=fields.Integer("Total Expense")
    comment=fields.Text("Additional Information")
    state=fields.Selection([('draft','Draft'),('confirmed','Confirm'),
            ('validate1','First Approval'),('validate2','Second Approval'),('done','Ordered')])

    #sequence
    def create(self, cr, uid, vals, context=None):
        vals['planting_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.seeddo')
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
        self.action_receive()
        self.state = 'done'
    @api.one
    def action_receive(self):
         serial = self.env['estate.nursery.request'].search_count([]) + 1
         self.write({'name':"SPB %d" %serial})
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
    @api.depends('activityline_ids')
    def _amount_all(self):
        if self.activityline_ids:
            for price in self.activityline_ids:
                self.expense += price.result_price
        return True

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
                bpb_value_name = bpb.bpb_many2many.name
                if bpb_value_name in temp.values():
                    error_msg = "Request Seed \"%s\" is set more than once " % bpb_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[bpb.id] = bpb_value_name
            return temp

class ActivityLine(models.Model):
    _name = "estate.nursery.activityline"

    name=fields.Char()
    seeddo_id=fields.Many2one('estate.nursery.seeddo')
    activity_id=fields.Many2one('estate.activity')
    product_type_id=fields.Many2one('product.uom')
    price=fields.Float("Price/Quantity")
    qty_product=fields.Integer("Quantity Product Transfer")
    transportactivity_expense_id = fields.Many2one('account.account', "Expense Account",
                                         help="This account will be used for invoices to value expenses")
    result_price=fields.Float("Quantity Result",compute="calculate_price")

    @api.one
    def change_name(self):
        serial=self.env['estate.nursery.activityline'].search_count([])+ 1
        self.write({'name':"Activity %d" % serial})

    @api.one
    @api.depends('qty_product','price')
    def calculate_price(self):
        price=float(self.price)
        product=int(self.qty_product)
        if self.qty_product and self.price:
            result=price*product
            self.result_price=result
        return True

class Requestplanting(models.Model):
    #request seed to plant
    #delegation purchase order to BPB
    _name = "estate.nursery.request"
    _description = "Request Purchase Seed"
    _inherit = ['mail.thread']

    # _inherits = {'purchase.order': 'purchase_id',}


    name=fields.Char("Request code")
    bpb_code = fields.Char("BPB")
    user_id=fields.Many2one('res.users')
    batch_id=fields.Many2one('estate.nursery.batch')
    requestline_ids=fields.One2many('estate.nursery.requestline','request_id',"RequestLine")
    partner_id=fields.Many2one('res.partner',required=True, ondelete="restrict",
                               default=lambda self: self.partner_id.search
                                        ([('name','=','Dami Mas Sejahtera')]),track_visibility='onchange')
    picking_id=fields.Many2one('stock.picking', "Picking", readonly=True ,)
    kebun_location_id = fields.Many2one('estate.block.template',"Estate Location",track_visibility='onchange',
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '1'),
                                                  ],
                                        default=lambda self: self.kebun_location_id.search
                                        ([('name','=','LYD')]))
    divisi_location_id = fields.Many2one('estate.block.template',"Divisi Location",track_visibility='onchange',
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '2'),
                                                  ],
                                        default=lambda self: self.divisi_location_id.search
                                        ([('name','=','Division 1')]))
    date_request=fields.Date("Date Request",track_visibility='onchange')
    variety_id=fields.Many2one('estate.nursery.variety',required=True,track_visibility='onchange',
                               default=lambda self: self.variety_id.search
                                        ([('name','=','Dura')]))
    comment=fields.Text("Cause Pending")
    total_qty_pokok = fields.Integer("Quantity Pokok Bibit",compute="_compute_total",track_visibility='onchange')
    state=fields.Selection([('draft','Draft'),('open2','Open Pending'),('pending2','Pending'),
            ('pending','Pending'),('confirmed','Confirm'),('open','Open Pending'),
            ('validate1','First Approval'),('validate2','Second Approval'),('done','Draft To SPB')])

    #state
    @api.one
    def action_draft(self):
        """Set planting State to Draft."""
        self.state = 'draft'
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
    def action_confirmed(self):
        """Set Planting state to Confirmed."""
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
        self.action_receive()
        self.state = 'done'

    @api.one
    def action_receive(self):
        qty_req = self.total_qty_pokok
        requestlineids = self.requestline_ids
        serial = self.env['estate.nursery.request'].search_count([]) + 1

        for item in requestlineids:
            qty_req += item.qty_request
        self.write({'total_qty_pokok': self.total_qty_pokok,'name': "Request Seed  %d" % serial,})
        return True

    #compute RequestLine
    @api.one
    @api.depends('requestline_ids')
    def _compute_total(self):
        self.total_qty_pokok = 0
        if self.requestline_ids:
            for item in self.requestline_ids:
                self.total_qty_pokok += item.qty_request
        return True

    #sequence
    def create(self, cr, uid, vals, context=None):
        vals['bpb_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.request')
        res=super(Requestplanting, self).create(cr, uid, vals)
        return res

    # #datetime
    # @api.one
    # @api.depends("date_request")
    # def _report_date(self):
    #     today = datetime.now()
    #     self.date_request=today



# class SeedDoLine(models.Model):
#     _inherit = "estate.nursery.request"
#
#     seeddoline_id= fields.Many2one("estate.nursery.seeddo")

class RequestLine(models.Model):
    _name = "estate.nursery.requestline"

    name=fields.Char("Requestline",related='request_id.name')
    request_id=fields.Many2one('estate.nursery.request')
    inherit_location_id = fields.Many2one('estate.block.template', "Block",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '2'),
                                          ('estate_location_type', '=', 'planted'),
                                          ('scrap_location', '=', False)],
                                  help="Fill in location seed planted.",)
    Luas = fields.Float("Luas Block",digits=(2,2),related='inherit_location_id.area_planted',readonly=True)
    qty_request = fields.Integer("Quantity Request",required=True)
    comment = fields.Text("Decription / Comment")

class RepositorySeed(models.TransientModel):

    _name = 'repository.seed.batch'

    name=fields.Char()
    comment=fields.Char()


    def act_cancel(self, cr, uid, ids, context=None):
        #self.unlink(cr, uid, ids, context)
        return {'type':'ir.actions.act_window_close' }

    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }

class EstateSPB(models.Model):
    _name = 'estate.spb'
    _inherits = {'estate.nursery.seeddo': 'seed_template_id'}

    seed_template_id = fields.Many2one('estate.nursery.seeddo', "Batch Template")
    parameter_value_ids = fields.Many2many('estate.bpb.value', id1='batch_id', id2='val_id',
                                           string="Parameter Value")

class ParameterValue(models.Model):
    """Selection value for Parameter.
    """
    _name = 'estate.bpb.value'

    name = fields.Char('Value', translate=True, required=True)
    parameter_id = fields.Many2one('estate.nursery.request', "Parameter", ondelete='restrict')

class BatchParameter(models.Model):
    """Parameter of Batch.
    """
    _name = 'estate.batch.parameter'
    _inherit=['mail.thread']

    bpb_many2many=fields.Many2many('estate.nursery.request','bpb_spb_rel','request_id','val_id','BPB Form')
    total_qty_pokok = fields.Integer('Qty Request', compute="calculate_qty",track_visibility='onchange')
    batch_id = fields.Many2one('estate.nursery.batch', "Nursery Batch",
                               domain=[('selection_count','>=',6),('qty_planted','>',0),('age_seed_grow','>=', 6)],
                               track_visibility='onchange')
    from_location_id = fields.Many2many('estate.block.template','batch_rel_loc','inherit_location_id','batch_id', "From Location",
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),
                                                  ('scrap_location', '=', False),
                                                  ])
    parameter_value_id = fields.Many2one('estate.bpb.value', "Value",
                                         domain="[('parameter_id', '=', parameter_id)]",
                                         ondelete='restrict')

    #Compute Quantity from BPB
    @api.one
    @api.depends('bpb_many2many')
    def calculate_qty(self):
        if self.bpb_many2many:
            for item in self.bpb_many2many:
                self.total_qty_pokok += item.total_qty_pokok

class TransferSeed(models.TransientModel):

    _name = "estate.nursery.transfer"

    # @api.one
    # def do_detailed_transfer(self):
    #     """
    #     Extend stock transfer wizard to create stock move and lot.
    #     """
    #     date_done = self.picking_id.date_done
    #
    #     # Iterate through transfer detail item
    #     for item in self.item_ids:
    #         if item.product_id.seed:
    #             if date_done or item.variety_id or item.progeny_id:
    #                 lot_new = self.do_create_lot(item.product_id)
    #                 item.write({'lot_id': lot_new[0].id})
    #                 batch = self.do_create_batch(item, self, lot_new[0])
    #                 self.do_create_batchline(item, batch[0])
    #             else:
    #                 raise exceptions.Warning('Required Date of Transfer, Variety and Progeny.')
    #         super(TransferSeed, self).do_detailed_transfer()
    #
    #     return True



class DetailTransferSeed(models.TransientModel):

    _inherit= "estate.nursery.transfer"

    qty_difference=fields.Integer('Quantity Difference',track_visibility='onchange')
    qty_result=fields.Integer('Quantity Result',track_visibility='onchange')


    #onchange field
    # @api.one
    # @api.onchange('qty_result','qty_difference','total_qty_pokok ')
    # def onchange_qty_result(self):
    #     if self.total_qty_pokok:
    #         self.qty_result = self.total_qty_pokok - self.qty_difference
    #         self.write({'qty_result' : self.qty_result})
