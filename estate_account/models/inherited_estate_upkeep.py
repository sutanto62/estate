# -*- coding: utf-8 -*-

import logging
from openerp import models, fields, api, _
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
import pytz
from openerp.exceptions import ValidationError
from lxml import etree

class UpkeepLabor(models.Model):
    """ Get labour cost by move line"""
    _inherit = 'estate.upkeep.labour'

    def get_quantity(self, vals):
        """
        Quantity defined in upkeep labour.
        :param start: start date of payslip batch
        :param end: end date of payslip batch
        :param analytic: analytic account ID
        :param account: general account ID
        :param company: location company ID
        :param employee_ids: employee ids
        :return: quantity, product_uom_id
        :rtype: dict
        """

        labour_obj = self.env['estate.upkeep.labour']
        activity_obj = self.env['estate.activity']
        labour_ids = labour_obj.search([('upkeep_date', '>=', vals['start']),
                                        ('upkeep_date', '<=', vals['end']),
                                        ('planted_year_id.analytic_account_id', "=", vals['analytic']),
                                        ('general_account_id', '=', vals['account']),
                                        ('company_id', '=', vals['company']),
                                        ('employee_id', 'in', vals['employee_ids']),
                                        ('state', 'in', ('approved', 'correction', 'payslip')),
                                        ('activity_id.is_productivity', '=', 'True')])
        quantity = 0.0
        uom_ids = []
        for labour in labour_ids:
            wage_method = labour.activity_id.wage_method
            activity = labour.activity_id
            if wage_method == 'standard' and labour.activity_contract:
                quantity = quantity + activity.convert_quantity(labour.quantity_piece_rate)
            else:
                quantity = quantity + activity.convert_quantity(labour.quantity)
            uom_ids.append(labour.activity_id.productivity_uom_id)

        uom = set(uom_ids).pop().id if set(uom_ids) else ''

        res = {
            'quantity': quantity,
            'productivity_uom_id': uom
        }

        return res


