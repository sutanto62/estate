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

    type_asset = fields.Selection([('1','Vehicle'), ('2','Building'),
                                   ('3','Machine'),('4','Computing'),('5','Tools'),('6','ALL')])
    fleet_id = fields.Many2one('fleet.vehicle')
    product_id = fields.Many2one('product.template')
    asset_value = fields.Float()

    #onchange
    @api.multi
    @api.onchange('name','fleet_id','product_id')
    def _onchange_name(self):
        if self.fleet_id:
            self.name = self.fleet_id.name
        if self.product_id:
            self.name = self.product_id.name

    @api.multi
    @api.onchange('asset_value','fleet_id','product_id')
    def _onchange_name(self):
        if self.product_id:
            self.asset_value = self.product_id.standard_price
        if self.fleet_id:
            self.asset_value = self.fleet_id.car_value

    @api.multi
    @api.onchange('product_id','type_asset')
    def _onchange_product_id(self):
        arrProduct = []
        if self.type_asset == '5':
            product = self.env['product.template'].search([('type','=','product'),('type_tools','=','1')])
            for idproduct in product:
                arrProduct.append(idproduct.id)
            return {
                    'domain' : {
                        'product_id' : [('id','in',arrProduct)]
                    }
                }
        if self.type_asset == '3':
            product =  self.env['product.template'].search([('type','=','product'),('type_machine','=','1')])
            for idproduct in product:
                arrProduct.append(idproduct.id)
            return {
                'domain' : {
                        'product_id' : [('id','=',arrProduct)]
                    }
                }

class InheritTypetoolsProductTemplate(models.Model):

    _inherit ='product.template'

    type_tools = fields.Boolean('Type Tools',default=False)
    type_machine = fields.Boolean('Type Machine',default=False)

