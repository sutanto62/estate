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

class EquipmentMaintenanceOrder(models.Model):

    _name = 'equipment.maintenance.order'
    _description = 'Parent Equipment Maintenance Order'

    name = fields.Char('Parent Equipment')
    asset_id = fields.Many2one('asset.asset','Asset',domain=[('type_asset', '=', '5')])
    mro_id = fields.Integer('MRO')
    ownership = fields.Selection([('1','Internal'),('2','External')])
    uom_id = fields.Many2one('product.uom','UOM',store=True)
    unit_actual = fields.Float('Unit',digits=(2,2))
    unit_plan = fields.Float('Unit',digits=(2,2))
    description = fields.Text('Description')

class ActualEquipment(models.Model):

    _name = 'estate.workshop.actualequipment'
    _inherits = {'equipment.maintenance.order':'parenttool_id'}
    _description = 'Actual Equipment'


    name = fields.Char('Actual Equipment')
    parenttool_id = fields.Many2one('equipment.maintenance.order',required=True,ondelete='cascade')

    @api.multi
    @api.onchange('uom_id','asset_id')
    def _onchange_uom_id(self):
        """ Finds UoM and UoS of changed product.
        @param product_id: Changed id of product.
        @return: Dictionary of values.
        """
        arrUom = []
        if self.asset_id:
            w = self.env['product.template'].search([('id','=',self.asset_id.product_id.id)])
            self.uom_id = w.uom_id.id



class PlannedEquipment(models.Model):

    _name = 'estate.workshop.plannedequipment'
    _inherits = {'equipment.maintenance.order':'parenttool_id'}
    _description = 'Planned Equipment'

    name=fields.Char('Planned Tools')
    parenttool_id = fields.Many2one('equipment.maintenance.order',required=True,ondelete='cascade')

    @api.multi
    @api.onchange('uom_id','asset_id')
    def _onchange_uom_id(self):
        """ Finds UoM and UoS of changed product.
        @param product_id: Changed id of product.
        @return: Dictionary of values.
        """
        if self.asset_id:
            w = self.env['product.template'].search([('id','=',self.asset_id.product_id.id)])
            self.uom_id = w.uom_id.id
