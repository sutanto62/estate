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


# class AbstractProcurement(models.Model):

    # #Method Get user
    # @api.multi
    # def _get_user(self):
    #     #find User
    #     user= self.env['res.users'].browse(self.env.uid)
    #
    #     return user
    #
    # @api.multi
    # def _get_employee(self):
    #     #find User Employee
    #
    #     employee = self.env['hr.employee'].search([('user_id','=',self._get_user().id)])
    #
    #     return employee
    #
    # @api.multi
    # def _get_user_manager(self):
    #     #Find Employee user Manager
    #     employeemanager = self.env['hr.employee'].search([('user_id','=',self._get_user().id)]).parent_id.id
    #     assigned_manager = self.env['hr.employee'].search([('id','=',employeemanager)]).user_id.id
    #
    #     return assigned_manager

    # @api.multi
    # def _get_office_level_id(self):
    #
    #     try:
    #         employee = self._get_employee().office_level_id.name
    #     except:
    #         raise exceptions.ValidationError('Office level Is Null')
    #
    #     return employee
    #
    # @api.multi
    # def _get_office_level_id_code(self):
    #
    #     try:
    #         employee = self._get_employee().office_level_id.code
    #     except:
    #         raise exceptions.ValidationError('Office level Is Null')
    #
    #     return employee
    #
    # _name = 'abstract.procurement'


