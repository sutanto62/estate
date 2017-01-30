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
    type_functional = fields.Selection([('agronomy','Agronomy'),
                                     ('technic','Technic'),('general','General')],'Unit Functional')
    department_id = fields.Many2one('hr.department')
    product_category_id = fields.Many2one('product.category',domain=[('parent_id','!=',False),('type','=','normal')])
    assigned_id = fields.Many2one('hr.job','Approver')

    @api.multi
    @api.onchange('type_functional')
    def _onchange_department(self):
        arrDepartment = []
        if self.type_functional == 'agronomy':
            department = self.env['hr.department'].search([('name','in',['agronomi','Agronomi',
                                                                         'Agronomy','agronomy','PR & LA','Pr & La',
                                                                         'PR&LA','pr & la','pr&la'])])
            for department in department:
                arrDepartment.append(department.id)
            return {
                'domain':{
                    'department_id':[('id','in',arrDepartment)]
                }
            }
        if self.type_functional == 'technic':
            department = self.env['hr.department'].search([('name','in',['IE','transport & workshop','Transport & Workshop'])])
            for department in department:
                arrDepartment.append(department.id)
            return {
                'domain':{
                    'department_id':[('id','in',arrDepartment)]
                }
            }
        if self.type_functional == 'general':
            department = self.env['hr.department'].search([('name','in',['HR & GA','HR','GA',
                                                                         'ICT','Finance','Legal','Procurement','GIS','RO'])])
            for department in department:
                arrDepartment.append(department.id)
            return {
                'domain':{
                    'department_id':[('id','in',arrDepartment)]
                }
            }

