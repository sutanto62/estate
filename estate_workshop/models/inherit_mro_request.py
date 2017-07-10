from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import os,fnmatch
import calendar
import time
import math
import tempfile
import base64

from PIL import Image
import datetime
from openerp import tools


class InheritTypeAsset(models.Model):

    @api.multi
    def get_ir_params(self):
        for ir_params in self:
            params = ir_params.env['ir.config_parameter']
            params_key = params.search([('key','=',self._name)]).value
            floating_params_key = float(params_key)

            return floating_params_key

    @api.multi
    def get_params(self):
        for request in self:

            if request.get_ir_params() == 0:
               return 0
            int_params = int(math.floor(math.log(request.get_ir_params(), 1024)))
            p = math.pow(1024, int_params)
            result = round(request.get_ir_params() / p, 2)

            return  result

    @api.multi
    def get_params_name(self):
        for params in self:

            if params.get_ir_params() == 0:
               return "0B"
            size_params_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
            int_params = int(math.floor(math.log(params.get_ir_params(), 1024)))

            return "%s " % (size_params_name[int_params])

    _inherit =  'mro.request'
    _description = 'Notification workshop for corrective Maintenance'

    code_id = fields.Many2one('estate.workshop.causepriority.code','Cause Failure',domain=[('type', '=', '1')],
                             states={'draft':[('readonly',False)],'run':[('readonly',True)],
                                'claim':[('readonly',True)],'done':[('readonly',True)],'cancel':[('readonly',True)]})
    typetask_id = fields.Many2one('estate.master.type.task','Type Task',domain=[('parent_id','=',False)],
                                 states={'draft':[('readonly',False)],'run':[('readonly',True)],
                                'claim':[('readonly',True)],'done':[('readonly',True)],'cancel':[('readonly',True)]})
    type_asset = fields.Selection([('1','Vehicle'),
                                     ('2','Building'),('3','Machine'),
                                   ('4','Computing'),('5','Tools'),('6','ALL')],compute='_onchange_type_asset',readonly=True)
    image = fields.Binary('Image',size=256,help="Select image here")
    image_filename=fields.Char('Filename')
    category_unit_id = fields.Integer('Category')
    category_name = fields.Char('Category',compute='_onchange_category_unit_name')


    #onchange type Asset
    @api.multi
    @api.depends('asset_id','type_asset')
    def _onchange_type_asset(self):
        if self.asset_id:
            self.type_asset = self.asset_id.type_asset

    @api.multi
    @api.onchange('category_unit_id','asset_id')
    def _onchange_category_unit_id(self):
        for record in self:
            if record.asset_id:
                record.category_unit_id = record.asset_id.category_unit_id

    @api.multi
    @api.depends('category_name','asset_id')
    def _onchange_category_unit_name(self):
        for record in self:
            if record.asset_id:
                record.category_name = record.asset_id.category_name

    #onchange Cause
    @api.multi
    @api.onchange('code_id','cause')
    def _onchange_cause(self):
        if self.code_id:
            self.cause = self.code_id.name

    @api.multi
    @api.onchange('description','code_id')
    def _onchange_description(self):
        if self.code_id:
            self.cause = self.code_id.name

    @api.multi
    def convert_size(self):
        for request in self:
             """"
                Convert and Constraint upload file size

                Input : * ir.config_parameter
                        * insert key like _name models
                        example : mro.request
                        * insert value type Integer 'bytes'
                        example : 307200

                get location of path file drom binary upload odoo.
                get size of file

             """
             size_bytes = len(request.image.decode('base64'))

             if size_bytes == 0:
               return "0B"
             size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
             i = int(math.floor(math.log(size_bytes, 1024)))
             p = math.pow(1024, i)
             s = round(size_bytes / p, 2)

             substring_target_type = "%s" % (size_name[i])
             name_params = request.get_params_name()

             if str(substring_target_type) == str(name_params):
                 if float(s) > float(request.get_params()):
                     return False
                 else:
                     return True
             else:
                 if substring_target_type in ("MB", "GB", "TB", "PB", "EB", "ZB", "YB"):
                     return False
                 elif substring_target_type in ("B"):
                     if float(size_bytes) > request.get_ir_params():
                         return False
                 else:
                     if float(s) > float(request.get_params()):
                        return False
                     else:
                        return True

    @api.multi
    def action_send(self):
        for request in self:

             if request.requester_id.id == False:
                error_msg = "Requester Field Must be Filled"
                raise exceptions.ValidationError(error_msg)
             if request.code_id.id == False:
                error_msg = "Cause Failure Must be Filled"
                raise exceptions.ValidationError(error_msg)
             if request.typetask_id.id == False:
                error_msg = "Maintenance Type Must be Filled"
                raise exceptions.ValidationError(error_msg)
             if request.location_id.id == False:
                error_msg = "Accident Location Must be Filled"
                raise exceptions.ValidationError(error_msg)
             if request.image == None:
                error_msg = "Accident Image Must be Filled"
                raise exceptions.ValidationError(error_msg)
             if request.convert_size() == False:
                param = request.get_params()
                error_msg = "Accident Image Must less than %s %s"%(param,request.get_params_name())
                raise exceptions.ValidationError(error_msg)
             super(InheritTypeAsset,self).action_send()

    @api.multi
    def action_confirm(self):
        """
        Update type_service into approved
        :return: True
        """
        for request in self:
            super(InheritTypeAsset, self).action_confirm_custom()