from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar


class Culling(models.Model):

    _name = "estate.nursery.culling"

    name=fields.Char("Culling Name",)
    culling_code=fields.Char("LBP")
    cullingline_ids=fields.One2many('estate.nursery.cullingline','culling_id',"Culling")
    culling_date = fields.Date("Culling date",)
    batch_id=fields.Many2one('estate.nursery.batch')
    picking_id = fields.Many2one('stock.picking', "Picking", readonly=True )
    # lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
    #                          domain=[('product_id.seed','=',True)])
    # product_id = fields.Many2one('product.product', "Product", related="lot_id.product_id")
    # stockquant_id=fields.Many2one('stock.quant',
    #                               domain=[('location_id.estate_location_type', '=', 'nursery'),
    #                                       ('location_id.scrap_location','=',True),
    #                                       ('location_id.estate_location_level', '=', '3')],store=True)
    quantitytotal_abnormal = fields.Integer("Quantity Total Abnormal",compute='_compute_total',store=True)
    culling_location_id = fields.Many2one('stock.location',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),('scrap_location', '=', True)]
                                          ,store=True)
    state= fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),('approved1','First Approval '),('approved2','Second Approval'),
        ('done', 'Done')],string="Culling State")


    #sequence
    def create(self, cr, uid, vals, context=None):
        vals['culling_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.culling')
        res=super(Culling, self).create(cr, uid, vals)
        return res

    #calculate Culling Line
    @api.one
    @api.depends('cullingline_ids')
    def _compute_total(self):
        self.quantitytotal_abnormal = 0
        for item in self.cullingline_ids:
            self.quantitytotal_abnormal += item.qty_abnormal
        return True


    @api.one
    def action_draft(self):
        """Set Selection State to Draft."""
        self.state = 'draft'

    @api.one
    def action_confirmed(self):
        """Set Selection state to Confirmed."""
        self.state = 'confirmed'

    @api.one
    def action_approved1(self):
        """Set Selection state to Confirmed."""
        self.state = 'approved1'

    @api.one
    def action_approved2(self):
        """Set Selection state to Confirmed."""
        self.state = 'approved2'

    @api.one
    def action_approved(self):
        """Approved Selection is planted Seed."""
        # self.action_receive()
        self.state = 'done'

    @api.one
    def action_receive(self):
        abnormal = self.quantitytotal_abnormal
        cullinglineids = self.cullingline_ids
        for item in cullinglineids:
            abnormal += item.qty_abnormal
        self.write({'quantitytotal_abnormal': self.quantitytotal_abnormal })
        # self.action_move()
        return True

    # @api.one
    # def action_move(self):
    #      if self.qty_abnormal > 0:
    #         move_data = {
    #             'product_id': self.batch_id.product_id.id,
    #             'product_uom_qty': self.quantitytotal_abnormal,
    #             'product_uom': self.batch_id.product_id.uom_id.id,
    #             'name': 'Selection Abnormal.%s: %s'%(self.selectionstage_id.name,self.lot_id.product_id.display_name),
    #             'date_expected': self.date_plant,
    #             'location_id': self.picking_id.location_dest_id.id,
    #             'location_dest_id': self..id,
    #             'state': 'confirmed', # set to done if no approval required
    #             'restrict_lot_id': self.lot_id.id # required by check tracking product
    #         }
    #
    #         move = self.env['stock.move'].create(move_data)
    #         move.action_confirm()
    #         move.action_done()
    #      return True


class Cullingline(models.Model):

    _name = "estate.nursery.cullingline"

    name=fields.Char("Culling line name",related='culling_id.name')
    culling_id=fields.Many2one('estate.nursery.culling')
    stock_id=fields.Many2one('stock.quant')
    stockquant_id=fields.Many2one('stock.quant',
                                  store=True,domain=[('location_id.estate_location_type', '=', 'nursery'),
                                          ('location_id.scrap_location','=',True),
                                          ('location_id.estate_location_level', '=', '3')])
    qty_abnormal=fields.Integer('Quantity Abnormal')
    # domain=[('location_id.estate_location_type', '=', 'nursery'),
    #                                       ('location_id.scrap_location','=',True),
    #                                       ('location_id.estate_location_level', '=', '3')]
    # # related='stockquant_id.stock_id.qty
    # compute='ChangeQuantity'

    #search qty stock quant
    @api.onchange('stockquant_id','qty_abnormal')
    def ChangeQuantity(self):
        self.qty_abnormal=self.stockquant_id.qty
        self.write({'qty_abnormal': self.qty_abnormal, })
        print self.qty_abnormal


    # @api.one
    # def search_qty_quant(self):
    #     location_stockids = set()
    #     for qty in self.stockquant_id:
    #         qty=0
    #         stock=self.env['stock.quant'].browse([('location_id.estate_location_type','=','nursery'),('qty','=',True)])
    #         print stock

    # related='stockquant_id.lot_id.qty',relation='stock.quant',store=True

class StockQuant(models.Model):

    _name="estate.nursery.stock"
    _inherits = {'stock.quant':'stockquant_id'}


    stockquant_id = fields.Many2one('stock.quant')
    qty=fields.Integer()







    