from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
import time
import datetime
from openerp import tools


class InheritTypeAsset(models.Model):

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
    image = fields.Binary('Image',help="Select image here")



    #onchange type Asset
    @api.multi
    @api.depends('asset_id','type_asset')
    def _onchange_type_asset(self):
        if self.asset_id:
            self.type_asset = self.asset_id.type_asset

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
             super(InheritTypeAsset,self).action_send()

    @api.multi
    def action_confirm(self):
        """
        Update type_service into approved
        :return: True
        """
        for request in self:
            super(InheritTypeAsset, self).action_confirm_custom()