from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re



class ServiceReceiptNote(models.Model):

    _inherit= 'stock.picking'

    complete_name_picking =fields.Char("Complete Name", compute="_complete_name_picking", store=True)

    @api.one
    @api.depends('grn_no','min_date','companys_id','type_location')
    def _complete_name_picking(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d %H:%M:%S'
        if self.purchase_id.request_id.type_product == 'service':
            if self.min_date and self.companys_id.code and self.type_location:
                date = self.min_date
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

                self.complete_name_picking = self.grn_no +'/' \
                                     + self.companys_id.code+'-'\
                                     +'SRN'+'/'\
                                     +str(self.type_location)+'/'+str(month)+'/'+str(year)
            else:
                self.complete_name_picking = self.name
        else:
            super(ServiceReceiptNote,self)._complete_name_picking()

        return True

    @api.multi
    def do_new_transfer(self):
        for item in self:
            if item.purchase_id.request_id.type_product == 'service':
                item.write({'state':'done'})
            else:
                super(ServiceReceiptNote,self).do_new_transfer()

