from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar

class Planting(models.Model):
    #seed planting
    _name = "estate.nursery.planting"
    _inherits = {'stock.production.lot': 'lot_id'}

    name=fields.Char("Planting Code")
    planting_code=fields.Char("Planting Code")
    request_id=fields.Many2one('estate.nursery.request')
    product_id = fields.Many2one('product.product', "Product", related="lot_id.product_id")
    picking_id = fields.Many2one('stock.picking', "Picking", readonly=True ,)
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)])
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety", required=True, ondelete="restrict",
                                 related="request_id.variety_id",readonly=True)
    progeny_id = fields.Many2one('estate.nursery.progeny', "Seed Progeny", required=True, ondelete="restrict",
                                 domain="[('variety_id','=',variety_id)]")
    kebun_location_id = fields.Many2one('stock.location',"Estate Location",
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '1'),
                                                  ],
                                        default=lambda self: self.kebun_location_id.search
                                        ([('name','=','Liyodu Estate')]))
    divisi_location_id = fields.Many2one('stock.location',"Divisi Location",
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '2'),
                                                  ],
                                        default=lambda self: self.divisi_location_id.search
                                        ([('name','=','Pembibitan Liyodu')]))
    plantingline_ids=fields.One2many('estate.nursery.plantingline','planting_id',"Planting line")
    date_received = fields.Date("Received Date",required=False,readonly=True)
    date_request = fields.Date(related="request_id.date_request")
    date_planted = fields.Date("Planted Date",required=False,readonly=False)
    total_qty_pokok= fields.Date("Total Pokok")
    state=fields.Selection([('draft','Draft'),('confirmed','Confirm'),
            ('validate1','First Approval'),('validate2','Second Approval'),('done','Ordered')])

    #sequence
    def create(self, cr, uid, vals, context=None):
        vals['planting_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.planting')
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
        # self.action_receive()
        self.state = 'done'

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

class PlantingLine(models.Model):

    _name = "estate.nursery.plantingline"
    _description = "Planting Line (Blok)"
    _parent_store = True
    _parent_name = "parent_id"
    _parent_order = "name"


    name=fields.Char("PlantingLine")
    parent_id = fields.Many2one('estate.nursery.plantingline', "Parent Package", ondelete="restrict")
    parent_left = fields.Integer('Parent Left', index=True)
    parent_right = fields.Integer('Parent Right', index=True)
    child_ids = fields.One2many('estate.nursery.plantingline', 'parent_id', "Contains")
    planting_id=fields.Many2one("estate.nursery.planting")

class Requestplanting(models.Model):
    #request seed to plant
    #delegation purchase order to BPB
    _name = "estate.nursery.request"

    # _inherits = {'purchase.order': 'purchase_id',}


    name=fields.Char("Request code",)
    bpb_code = fields.Char("BPB")
    purchase_id= fields.Many2one('purchase.order',"Purchase",required=True, ondelete="restrict",)
    user_id=fields.Many2one('res.users')
    batch_ids=fields.One2many("estate.nursery.batch","request_id")
    planting_id=fields.Many2one('estate.nursery.planting')
    requestline_ids=fields.One2many('estate.nursery.requestline','request_id',"RequestLine")
    partner_id=fields.Many2one('res.partner',required=True, ondelete="restrict",
                               default=lambda self: self.partner_id.search
                                        ([('name','=','Dami Mas Sejahtera')]))
    # respartner_id=fields.Many2one('res.partner',store=True)
    picking_id=fields.Many2one('stock.picking', "Picking", readonly=True ,)
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)],)
    product_id=fields.Many2one('product.product', "Product", related="lot_id.product_id")
    kebun_location_id = fields.Many2one('stock.location',"Estate Location",
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '1'),
                                                  ],
                                        default=lambda self: self.kebun_location_id.search
                                        ([('name','=','Liyodu Estate')]))
    divisi_location_id = fields.Many2one('stock.location',"Divisi Location",
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '2'),
                                                  ],
                                        default=lambda self: self.divisi_location_id.search
                                        ([('name','=','Pembibitan Liyodu')]))
    date_request=fields.Date("Date Request",compute="_report_date")
    variety_id=fields.Many2one('estate.nursery.variety')
    # batch_id=fields.Many2one('estate.nursery.batch')
    comment=fields.Text("Cause Pending")
    # qty_batch=fields.Integer(related='batch_id.qty_planted')
    total_qty_pokok = fields.Integer("Quantity Pokok Bibit",compute="_compute_total")
    state=fields.Selection([('draft','Draft'),('open2','Open Pending'),('pending2','Pending'),
            ('pending','Pending'),('confirmed','Confirm'),('open','Open Pending'),
            ('validate1','First Approval'),('validate2','Second Approval'),('done','Ordered')])

    #getstockonhand
    def get_quantity_at_location(self,cr,uid,lid,p):
        ls = ['stock_real','stock_virtual','stock_real_value','stock_virtual_value']
        move_avail = self.pool.get('stock.location')._product_value(cr,uid,[lid],ls,0,{'product_id':p})
        print move_avail
        return move_avail[lid]['stock_real']

    #calculatestockbatch



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

        for item in requestlineids:
            qty_req += item.qty_request
        self.write({'total_qty_pokok': self.total_qty_pokok})

        return True

    # @api.one
    # def action_move(self):
    #     # Move seed
    #     if self.total_qty_pokok > 0:
    #         move_data = {
    #             'product_id': self.batch_id.product_id.id,
    #             'product_uom_qty': self.total_qty_pokok,
    #             'product_uom': self.batch_id.lot_id.product_id.uom_id.id,
    #             'name': 'Request Seed .%s: %s'%(self.bpb_code,self.lot_id.product_id.display_name),
    #             'date_expected': self.date_request,
    #             'location_id': self.picking_id.location_dest_id.id,
    #             'location_dest_id': self.kebun_location_id.id,
    #             'state': 'confirmed', # set to done if no approval required
    #             'restrict_lot_id': self.lot_id.id # required by check tracking product
    #         }
    #
    #         move = self.env['stock.move'].create(move_data)
    #         move.action_confirm()
    #         move.action_done()
    #     return True

    # def _create_stock_moves(self, cr, uid, request, request_lines, picking_id=False, context=None):
    #     """Creates appropriate stock moves for given order lines, whose can optionally create a
    #     picking if none is given or no suitable is found, then confirms the moves, makes them
    #     available, and confirms the pickings.
    #
    #     If ``picking_id`` is provided, the stock moves will be added to it, otherwise a standard
    #     incoming picking will be created to wrap the stock moves (default behavior of the stock.move)
    #
    #     Modules that wish to customize the procurements or partition the stock moves over
    #     multiple stock pickings may override this method and call ``super()`` with
    #     different subsets of ``order_lines`` and/or preset ``picking_id`` values.
    #
    #     :param browse_record order: purchase order to which the order lines belong
    #     :param list(browse_record) order_lines: purchase order line records for which picking
    #                                             and moves should be created.
    #     :param int picking_id: optional ID of a stock picking to which the created stock moves
    #                            will be added. A new picking will be created if omitted.
    #     :return: None
    #     """
    #     stock_move = self.pool.get('stock.move')
    #     todo_moves = []
    #     new_group = self.pool.get("procurement.group").create(cr, uid, {'name': request.name, 'partner_id': request.partner_id.id}, context=context)
    #
    #     for request_line in request_lines:
    #         if request_line.state == 'cancel':
    #             continue
    #         if not request_line.product_id:
    #             continue
    #
    #         if request_line.request_id.type in ('product', 'consu'):
    #             for vals in self._prepare_request_line_move(cr, uid, request, request_lines, picking_id, new_group, context=context):
    #                 move = stock_move.create(cr, uid, vals, context=context)
    #                 todo_moves.append(move)
    #
    #     todo_moves = stock_move.action_confirm(cr, uid, todo_moves)
    #     stock_move.force_assign(cr, uid, todo_moves)

    #compute selectionLine
    @api.one
    @api.depends('requestline_ids')
    def _compute_total(self):
        self.total_qty_pokok = 0
        for item in self.requestline_ids:
            self.total_qty_pokok += item.qty_request
        return True

    #sequence
    def create(self, cr, uid, vals, context=None):
        vals['bpb_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.request')
        res=super(Requestplanting, self).create(cr, uid, vals)
        return res

    #datetime

    @api.one
    @api.depends("date_request")
    def _report_date(self):
        today = datetime.now()
        self.date_request=today


class RequestLine(models.Model):
    _name = "estate.nursery.requestline"

    name=fields.Char("Requestline",related='request_id.name')
    batch_id=fields.Many2one('estate.nursery.batch',required=True)
    request_id=fields.Many2one('estate.nursery.request')
    location_id = fields.Many2one('stock.location', "Bedengan/Plot",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '3'),
                                          ('estate_location_type', '=', 'nursery'),
                                          ('scrap_location', '=', False)],
                                  help="Fill in location seed planted.")
    Luas = fields.Float("Luas Block",digits=(2,2))
    qty_batch=fields.Integer(related='batch_id.qty_planted')
    qty_request = fields.Integer("Quantity Request",required=True)
    comment = fields.Text("Decription / Comment")

    # @api.one
    # @api.depends('qty_batch','qty_request')
    # def validateqty_batch(self):
    #
    #     if self.qty_request :
    #         if self.qty_request > self.qty_batch:
    #             raise exceptions.Warning('Quantity cannot Higger Than Quantity Batch %s. Review you quantity.' % self.batch_id.name)


class TrasferSeed(models.Model):

    _name = "estate.nursery.trasfer"

