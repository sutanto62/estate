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
import json
import logging
from operator import attrgetter
import re

class PurchaseInheritMroOrder(models.Model):

    _inherit = ['purchase.request']

    def _default_session(self):
        return self.env['mro.order'].browse(self._context.get('active_id'))

    mro_order_id = fields.Many2one('mro.order','Maintenance Order ID',default=_default_session)
    validation_mro = fields.Boolean('Validation MRO',default=False,compute='_change_validation_mro')

    @api.multi
    @api.depends('mro_order_id')
    def _change_validation_mro(self):
        for item in self:
            if item.mro_order_id.id :
                item.validation_mro = True
            else:
                item.validation_mro = False

    @api.multi
    @api.onchange('mro_order_id')
    def _onchange_type_functional(self):
        """For change Type functional and department if mro_order_id is True"""
        arrDepartment = []
        for item in self:
            if item.mro_order_id.id:
                item.type_functional = 'technic'

                department = self.env['hr.department'].search([('name','in',['IE','transport & workshop','Transport & Workshop'])])

                for department in department:
                    arrDepartment.append(department.id)

                return {
                    'domain':{
                        'department_id':[('id','in',arrDepartment)]
                    }
                }
