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



class InheritPurchaseRequestLine(models.Model):

    _inherit = 'purchase.request.line'

    @api.multi
    @api.onchange('request_id','product_id')
    def _onchange_product_purchase_request_line(self):
        #use to onchange domain product same as product_category
        for item in self:
            if item.request_id.type_functional and item.request_id.department_id:
                arrProductCateg = []
                mappingFuntional = item.env['mapping.department.product'].search([('type_functional','=',item.request_id.type_functional),
                                                                                  ('department_id.id','=',item.request_id.department_id.id)])

                for productcateg in mappingFuntional:
                    arrProductCateg.append(productcateg.product_category_id.id)

                arrProdCatId = []
                prod_categ = item.env['product.category'].search([('parent_id','in',arrProductCateg)])

                for productcategparent in prod_categ:
                    arrProdCatId.append(productcategparent.id)

                if item.type_product == 'service':
                    if prod_categ:
                        return  {
                            'domain':{
                                'product_id':[('type','=','service')]
                                 }
                            }
                    elif prod_categ != ():
                        return  {
                        'domain':{
                            'product_id':[('type','=','service')]
                             }
                        }
                elif item.type_product == 'product':
                    if prod_categ:
                        return  {
                            'domain':{
                                'product_id':[('categ_id','in',arrProdCatId),('type','!=','service')]
                                 }
                            }
                    elif prod_categ != ():
                        return  {
                        'domain':{
                            'product_id':[('categ_id','in',arrProductCateg),('type','!=','service')]
                             }
                        }

