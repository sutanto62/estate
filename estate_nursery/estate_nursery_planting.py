from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar

class Planting(models.Model):
    #seed planting
    _name = "estate.nursery.planting"

    name=fields.Char("Planting Code")
    request_ids=fields.One2many('estate.nursery.request','planting_id',"Request ")


class PlantingLine(models.Model):

    _name = "estate.nursery.plantingline"

class Requestplanting(models.Model):
    #request seed to plant
    #delegation purchase order to BPB
    _name = "estate.nursery.request"

    _inherits = {'purchase.order': 'purchase_id'}


    name=fields.Char("Request code",)
    bpb_code = fields.Char("BPB")
    purchase_id= fields.Many2one('purchase.order',"Purchase",required=True, ondelete="restrict",)
    user_id=fields.Many2one('res.users')
    batch_id=fields.Many2one('estate.nursery.batch',"Batch NO")
    planting_id=fields.Many2one('estate.nursery.planting')
    requestline_ids=fields.One2many('estate.nursery.requestline','request_id',"RequestLine")
    partner_id=fields.Many2one('res.partner')
    picking_id=fields.Many2one('stock.picking', "Picking", readonly=True ,)
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)],related="batch_id.lot_id")
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
    comment=fields.Text("Cause Pending")
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
    #             'product_id': self.batch_id.lot_id.product_id.id,
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
    request_id=fields.Many2one('estate.nursery.request')
    location_id = fields.Many2one('stock.location', "Bedengan/Plot",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '3'),
                                          ('estate_location_type', '=', 'nursery'),
                                          ('scrap_location', '=', False)],
                                  help="Fill in location seed planted.")
    Luas = fields.Float("Luas Block",digits=(2,2))
    qty_request = fields.Integer("Quantity Request")
    comment = fields.Text("Decription / Comment")


class TrasferSeed(models.Model):

    _name = "estate.nursery.trasfer"

