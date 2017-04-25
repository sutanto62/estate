from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re
import json
import logging
import time
from operator import attrgetter
import re


class InheritAccountInvoice(models.Model):

    _inherit = "account.invoice"

    picking_id = fields.Many2one('stock.picking','Picking ID')
    grn_srn_no = fields.Char('Goods or Service Receipt Note Number',related='picking_id.complete_name_picking')

class InheritAccountInvoiceLine(models.Model):

    _inherit = "account.invoice.line"

    picking_id = fields.Many2one('stock.picking','Picking ID',related='invoice_id.picking_id')
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'),
        required=True, default=1,compute='_onchange_quantity_with_picking_id',store=True)

    @api.multi
    @api.depends('picking_id','purchase_id')
    def _onchange_quantity_with_picking_id(self):
        for item in self:
            quantity_picking = 0
            if item.picking_id:
                for record in item.picking_id.pack_operation_product_ids:
                    quantity_picking = record.qty_done

                item.quantity = quantity_picking
            elif item.purchase_id and not item.picking_id:

                for record in item.purchase_id.order_line:
                    quantity_picking = record.product_qty

                item.quantity = quantity_picking
