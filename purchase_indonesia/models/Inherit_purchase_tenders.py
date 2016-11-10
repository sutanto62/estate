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


class InheritPurchaseTenders(models.Model):

    def return_action_to_open(self, cr, uid, ids, context=None):
        """ This opens the xml view specified in xml_id for the current Quotation Comparison """
        if context is None:
            context = {}
        if context.get('xml_id'):
            res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid ,'purchase_indonesia', context['xml_id'], context=context)
            res['context'] = context
            res['context'].update({'default_requisition_id': ids[0]})
            res['domain'] = [('requisition_id','=', ids[0])]
            return res
        return False

    _inherit = 'purchase.requisition'
    _description = 'inherit purchase requisition'

    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    type_location = fields.Selection([('KOKB','Estate'),
                                     ('KPST','HO'),('KPWK','RO')],'Location Type')
    companys_id = fields.Many2one('res.company','Company')

    @api.one
    @api.depends('name','schedule_date','company_id','type_location')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d'

        if self.name and self.schedule_date and self.company_id.code and self.type_location:
            date = self.schedule_date
            conv_date = datetime.strptime(str(date), fmt)
            month = conv_date.month
            year = conv_date.year

            #change integer to roman
            if type(month) != type(1):
                raise TypeError, "expected integer, got %s" % type(month)
            if not 0 < month < 4000:
                raise ValueError, "Argument must be between 1 and 3999"
            ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
            nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
            result = ""
            for i in range(len(ints)):
              count = int(month / ints[i])
              result += nums[i] * count
              month -= ints[i] * count
            month = result

            self.complete_name = self.name + ' / ' \
                                 + self.company_id.code+' - '\
                                 +'PQ'+' / '\
                                 +str(self.type_location)+'/'+str(month)+'/'+str(year)
        else:
            self.complete_name = self.name

        return True

    @api.multi
    def tender_in_progress(self):
       #overwrite button tender in progress on purchase requisition
       self.create_comparison()
       super(InheritPurchaseTenders, self).tender_in_progress()
       return True

    @api.multi
    def create_comparison(self):
        # create quotation comparison
        for purchase_tender in self:
            purchase_data = {
                'company_id': purchase_tender.companys_id.id,
                'date_pp': purchase_tender.schedule_date,
                'requisition_id': purchase_tender.id,
                'origin' : purchase_tender.origin,
                'type_location' : purchase_tender.type_location
            }
            self.env['quotation.comparison.form'].create(purchase_data)
        return True