from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re


class InheritPurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    validation_srn = fields.Boolean('Validation Product Type Service',default=False,compute='_change_validation_srn')


    @api.multi
    @api.depends('request_id')
    def _change_validation_srn(self):

        for item in self:

            if item.request_id.type_product == 'service':
                item.validation_srn = True
            else:
                item.validation_srn = False

    @api.multi
    def _create_picking(self):

        for order in self:
            if any([ptype in ['service'] for ptype in order.order_line.mapped('product_id.type')]):
                res = order._prepare_picking()
                picking = self.env['stock.picking'].create(res)
                moves = order.order_line.filtered(lambda r: r.product_id.type in ['service'])._create_stock_moves(picking)
                move_ids = moves.action_confirm()
                moves = self.env['stock.move'].browse(move_ids)
                moves.force_assign()
            else:
                super(InheritPurchaseOrder,self)._create_picking()
        return True