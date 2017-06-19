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


class InheritPurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    cheaper_code = fields.Selection([
            ('cheap','Cheaper'),
            ('expensive','Expensive'),
            ('medium','Medium')],'Cheaper Code',compute='_compute_cheaper')

    @api.multi
    @api.depends('product_id','product_qty','price_subtotal')
    def _compute_cheaper(self):
        for item in self:
            """
                Search price Cheaper
            """
            arrOrderMax = []
            arrOrderMin = []
            purchase_order_line = item.env['purchase.order.line']

            order_line_id = purchase_order_line.search([('comparison_id','=',item.comparison_id.id),
                                                     ('product_id','=',item.product_id.id)
                                                     ])

            min_price = min(price.price_unit for price in order_line_id)
            max_price = max(price.price_unit for price in order_line_id)


            order_line_max_id = purchase_order_line.search([('comparison_id','=',item.comparison_id.id),
                                                     ('product_id','=',item.product_id.id),
                                                     ('price_unit','=',max_price)])

            order_line_min_id = purchase_order_line.search([('comparison_id','=',item.comparison_id.id),
                                                     ('product_id','=',item.product_id.id),
                                                     ('price_unit','=',min_price)])

            for line in order_line_max_id:
                arrOrderMax.append(line.id)

            for line in order_line_min_id:
                arrOrderMin.append(line.id)


            for order  in order_line_id:
                if order.id in arrOrderMax:

                    order.cheaper_code = 'expensive'

                elif order.id in arrOrderMin:

                    order.cheaper_code = 'cheap'
                else:

                    order.cheaper_code = 'medium'

