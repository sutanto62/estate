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
from lxml import etree
from openerp.tools.translate import _


class MappingDepartmentToProduct(models.Model):

    _name = 'mapping.department.product'

    name= fields.Char('Name')
    department_id = fields.Many2one('hr.department')
    product_category_ids = fields.Many2many('product.category','department_product_category_rel','department_id','categ_id',string='Category Product')
    # product_category_id = fields.Many2one('product.category',domain=[('parent_id','!=',False),('type','=','normal')])
    assigned_to = fields.Many2one('res.users','Approver')

