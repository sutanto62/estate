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
    location_id = fields.Many2one('stock.location','Sub Location')
    assign_date = fields.Date('Assign Date')
    fleet_id = fields.Many2one('fleet.vehicle')
    product_id = fields.Many2one('product.template')
    account_id = fields.Many2one('account.account','General Account')
    asset_value = fields.Float()
    company_id = fields.Many2one('res.company','Company')
    category_unit_id = fields.Integer('Category ID',)
    category_name = fields.Char('Category Name',compute='_onchange_category_unit_name')

    #onchange
    @api.multi
    @api.onchange('name','fleet_id','product_id')
    def _onchange_name(self):
        if self.fleet_id:
            self.name = self.fleet_id.name
        if self.product_id:
            self.name = self.product_id.name

    # @api.multi
    # @api.onchange('fleet_id','category_unit_id')
    # def _onchange_category_unit(self):
    #     arrCategory=[]
    #     for item in self:
    #         if item.fleet_id:
    #             category = item.env['fleet.vehicle'].search([('id','=',item.fleet_id.id)])
    #             for category in category:
    #                 arrCategory.append(category.category_unit_id.id)
    #             return {
    #             'domain' : {
    #                 'category_unit_id' : [('id','in',arrCategory)]
    #             }
    #         }

    @api.multi
    @api.onchange('category_unit_id','fleet_id')
    def _onchange_category_unit_id(self):
        for record in self:
            if record.fleet_id:
                record.category_unit_id = record.fleet_id.category_unit_id

    @api.multi
    @api.depends('category_name','fleet_id')
    def _onchange_category_unit_name(self):
        for record in self:
            if record.fleet_id:
                record.category_name = record.fleet_id.category_unit_id.name

    @api.multi
    @api.onchange('fleet_id','category_unit_id')
    def _onchange_category_unit(self):
        arrCategory=[]
        for item in self:
            if item.fleet_id:
                category = item.env['fleet.vehicle'].search([('id','=',item.fleet_id.id)])
                for category in category:
                    arrCategory.append(category.category_unit_id.id)
                return {
                'domain' : {
                    'category_unit_id' : [('id','in',arrCategory)]
                }
            }

    @api.multi
    @api.onchange('asset_value','fleet_id','product_id')
    def _onchange_name(self):
        if self.product_id:
            self.asset_value = self.product_id.standard_price
        if self.fleet_id:
            self.asset_value = self.fleet_id.car_value

    #todo company structure
    # @api.multi
    # @api.onchange('fleet_id','company_id')
    # def _onchange_company(self):
    #     arrVehicle = []
    #     if self.fleet_id:
    #         vehicle = self.env['fleet.vehicle'].search([('id','=',self.fleet_id.id)])
    #         for vehicle in vehicle:
    #             arrVehicle.append(vehicle.company_id.id)
    #         return {
    #             'domain' : {
    #                 'company_id' : [('id','in',arrVehicle)]
    #             }
    #         }

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
        if self.type_asset == '4':
            product =  self.env['product.template'].search([('type','=','product'),('type_computing','=','1')])
            for idproduct in product:
                arrProduct.append(idproduct.id)
            return {
                'domain' : {
                        'product_id' : [('id','=',arrProduct)]
                    }
                }

    @api.multi
    @api.constrains('account_id','criticality','start_date','asset_number','model','type_asset','fleet_id','product_id','user_id')
    def _constraint_asset(self):
        for asset in self:
            # Todo di commend karena belum membutuhkan general account
            # if asset.account_id.id == False:
            #     error_msg = "General Account Must be Filled"
            #     raise exceptions.ValidationError(error_msg)
            if asset.type_asset == False:
                error_msg = "Type Asset Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if asset.type_asset == '5' or asset.type_asset == '3' or asset.type_asset == '6' or asset.type_asset == '4' :
                if asset.product_id.id == False:
                    error_msg = "Product Must be Filled"
                    raise exceptions.ValidationError(error_msg)
            if asset.type_asset == '1':
                if asset.fleet_id.id == False:
                    error_msg = "Vehicle Must be Filled"
                    raise exceptions.ValidationError(error_msg)
            if asset.criticality == False:
                error_msg = "Criticality Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if asset.user_id.id == False:
                error_msg = "Assigned Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if asset.asset_number == False:
                error_msg = "Asset Number Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if asset.model == False:
                error_msg = "Model Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if asset.start_date == False:
                error_msg = "Start Date Must be Filled"
                raise exceptions.ValidationError(error_msg)


class InheritTypetoolsProductTemplate(models.Model):

    _inherit ='product.template'

    type_tools = fields.Boolean('Type Tools',default=False)
    type_machine = fields.Boolean('Type Machine',default=False)
    type_computing = fields.Boolean('Type Computing',default=False)
    type_other = fields.Boolean('Type Other',default=False)

    @api.multi
    @api.constrains('type_tools','type_machine','type_computing','type_other')
    def _constraint_type(self):
        if self.type_tools and self.type_computing and self.type_machine and self.type_other:
            error_msg = "Product Type Not More Than one"
            raise exceptions.ValidationError(error_msg)
        elif self.type_tools and self.type_computing:
            error_msg = "Product Type Not More Than one"
            raise exceptions.ValidationError(error_msg)
        elif self.type_tools and self.type_machine:
            error_msg = "Product Type Not More Than one"
            raise exceptions.ValidationError(error_msg)
        elif self.type_computing and self.type_machine:
            error_msg = "Product Type Not More Than one"
            raise exceptions.ValidationError(error_msg)
        elif self.type_other and self.type_machine:
            error_msg = "Product Type Not More Than one"
            raise exceptions.ValidationError(error_msg)
        elif self.type_other and self.type_tools:
            error_msg = "Product Type Not More Than one"
            raise exceptions.ValidationError(error_msg)
        elif self.type_other and self.type_computing:
            error_msg = "Product Type Not More Than one"
            raise exceptions.ValidationError(error_msg)




