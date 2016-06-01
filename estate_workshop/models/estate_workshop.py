from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
import time
import datetime
from openerp import tools

class InheritSparepartLog(models.Model):

    _inherit='estate.vehicle.log.sparepart'

    maintenance_id = fields.Integer()

class InheritSparepartids(models.Model):

    _inherit = 'mro.order'

    type_service = fields.Selection([('1','Vehicle'),
                                     ('2','Building'),('3','Machine'),('4','Computing'),('5','ALL')],readonly=True)
    sparepartlog_ids=fields.One2many('estate.vehicle.log.sparepart','maintenance_id',"Part Log",
                                             readonly=True, states={'draft':[('readonly',False)]})

    #onchange
    @api.multi
    @api.onchange('asset_id','type_service')
    def onchange_type_service(self):
        if self.asset_id:
            self.type_service = self.asset_id.type_asset

# class NotificationWorkshop(models.Model):
#
#     _inherits = 'mro.order'



