from openerp import models, fields, api, exceptions, _
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar


class InheritStockQuant(models.Model):

    _name='estate.nursery.inherit.quant'
    _inherits = {'stock.quant' : 'stock_quant_id'}


    name=fields.Char()
    stock_quant_id=fields.Many2one('stock.quant')
    product_id=fields.Many2one('product.product')
    qty = fields.Integer('Quantity')
    lot_id = fields.Many2one('stock.production.lot')

    @api.onchange('qty')
    @api.depends( 'product_id','stock_quant_id')
    def _qty_product(self):
        for obj in self.stock_quant_id.product_id:
            self.qty = obj.qty