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



class InheritPurchaseRequestLine(models.Model):

    _inherit = 'purchase.request.line'

    # @api.multi
    # @api.onchange('request_id','product_id')
    # def _onchange_product_purchase_request_line(self):
    #
    #     for item in self:
    #
    #         if item.request_id.type_product == 'service':
    #
    #             product_id = item.env['product.template'].search([])