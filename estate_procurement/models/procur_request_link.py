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

class InheritPurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    owner_id = fields.Integer('owner id')


class InheritPurchaseRequest(models.Model):

    _inherit = 'purchase.request'

    type_purchase = fields.Selection([('1','Normal'),
                                     ('2','Urgent'),('3','Top Urgernt')],'Purchase Type')

    @api.multi
    def button_approved(self):
        self.create_purchase_requisition()
        super(InheritPurchaseRequest, self).button_approved()
        return True

    @api.multi
    def create_purchase_requisition(self):
        for purchase in self:
            purchase_data = {
                'responsible':purchase.requested_by.id,
                'origin': purchase.name,
                'ordering_date': purchase.date_start,
                'owner_id' : purchase.id
            }
            res = self.env['purchase.requisition'].create(purchase_data)


        for purchaseline in self.env['purchase.request.line'].search([('request_id.id','=',self.id)]):
            purchaseline_data = {
                'product_id': purchaseline.product_id.id,
                'product_uom_id': purchaseline.product_uom_id.id,
                'product_qty' : purchaseline.product_qty,
                'schedule_date' : purchaseline.date_start,
                'requisition_id' : res.id
            }
            self.env['purchase.requisition.line'].create(purchaseline_data)

        return True
