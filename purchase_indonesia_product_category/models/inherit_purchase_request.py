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
import itertools


class InheritPurchaseRequest(models.Model):

    _inherit = ['purchase.request']


    product_category_id = fields.Many2one('product.category',string='Product Category',domain=[('parent_id','!=',False)])

    @api.multi
    @api.onchange('department_id','type_functional')
    def _onchange_product_category_id(self):
        for item in self:
            mapping_department = item.env['mapping.department.product']
            arrMapping = []
            arrParent = []

            if item.department_id and item.type_functional:

                category_mapping = mapping_department.search([('department_id','=',item.department_id.id),
                                                              ('type_functional','=',item.type_functional)])

                for category in category_mapping:
                    arrMapping.append(category.product_category_id.id)
                    category_product = item.env['product.category'].search([('parent_id','in',arrMapping)])
                    arrParent.append(category.product_category_id.id)
                    if len(category_product) > 0:
                        for categ_id in category_product:
                            arrParent.append(categ_id.id)
                
                return  {
                        'domain':{
                            'product_category_id':[('id','in',arrParent)]
                             }
                        }


class InheritPurchaseRequestLine(models.Model):

    _inherit = ['purchase.request.line']

    @api.multi
    @api.onchange('request_id','product_id')
    def _onchange_product_purchase_request_line(self):
        #use to onchange domain product same as product_category
        for item in self:
            arrCategory = []

            prod_category = item.env['product.category']

            request_category = prod_category.search([('parent_id','=',item.request_id.product_category_id.id)])
            
            if len(request_category) == 0:
                request_category = prod_category.search([('id','=',item.request_id.product_category_id.id)])

            for category in request_category:
                arrCategory.append(category.id)


            if item.request_id.product_category_id.id:
                if item.request_id.type_product == 'service':
                        return  {
                            'domain':{
                                'product_id':[('categ_id','in',arrCategory),('type','=','service')]
                                 }
                            }
                elif item.request_id.type_product == 'consu':
                    return  {
                        'domain':{
                            'product_id':['&',('categ_id','in',arrCategory),'|',('type_machine','=',True),
                                                                          '|',('type_tools','=',True),
                                                                          '|',('type_other','=',True),
                                                                          ('type_computing','=',True)]
                             }
                        }
                elif item.request_id.type_product == 'product':
                    return  {
                        'domain':{
                            'product_id':['&',('categ_id','in',arrCategory),('type','=','product'),
                                                                        '&',('type_machine','=',False),
                                                                          '&',('type_tools','=',False),
                                                                          '&',('type_other','=',False),
                                                                          ('type_computing','=',False)]
                             }
                        }
                else:
                    return  {
                        'domain':{
                            'product_id':['&',('categ_id','in',arrCategory),('type','=','product'),
                                                                        '&',('type_machine','=',True),
                                                                          '&',('type_tools','=',True),
                                                                          '&',('type_other','=',True),
                                                                          ('type_computing','=',True)]
                             }
                        }
            else:
                super(InheritPurchaseRequestLine, item)._onchange_product_purchase_request_line()
