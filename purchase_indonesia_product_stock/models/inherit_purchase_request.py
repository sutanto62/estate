from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re
import itertools

class InheritPurchaseRequestLine(models.Model):

    _inherit = 'purchase.request.line'

    product_stock = fields.Float('Product Stock',compute='_change_get_qty_available')

    @api.multi
    @api.depends('product_id')
    def _change_get_qty_available(self):
        """"
        get stock from stock quant
        
        Search Domain Table : Stock.quant
                            : Stock.location
                            : product.product
                            : product.template
        """

        for record in self:
            if record.product_id:
               arrTemp =[]
               location_id = record.env['stock.location'].search([('usage','=','internal')])
               for item in location_id:
                   arrTemp.append(item.id)


               stock_quant_plus = record.env['stock.quant'].search([('product_id','=',record.product_id.id),('negative_move_id','=',None),('location_id','in',arrTemp)])
               stock_quant_min = record.env['stock.quant'].search([('product_id','=',record.product_id.id),('negative_move_id','!=',None),('location_id','in',arrTemp)])

               #get stock plus and stock negative
               stock_plus = sum(stock.qty for stock in stock_quant_plus)
               stock_min = sum(stock.qty for stock in stock_quant_min)

               total_quantity = stock_plus + stock_min

               record.product_stock = total_quantity