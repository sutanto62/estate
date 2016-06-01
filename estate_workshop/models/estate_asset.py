from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
import time
import datetime
from openerp import tools


class InheritAssetVehicle(models.Model):

    _inherit= 'asset.asset'
    _description = 'inherit fleet_id to asset management'

    type_asset = fields.Selection([('1','Vehicle'), ('2','Building'),('3','Machine'),('4','Computing'),('5','ALL')])
    fleet_id = fields.Many2one('fleet.vehicle')

    #onchange
    @api.multi
    @api.onchange('name','fleet_id')
    def _onchange_name(self):
        if self.fleet_id:
            self.name = self.fleet_id.name


