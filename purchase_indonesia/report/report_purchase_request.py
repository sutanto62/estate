#-*- coding:utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv
from openerp.report import report_sxw
from openerp import api, models
import math

class purchase_request_run_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(purchase_request_run_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_name_related': self.get_name_related,
        })

    #todo exercise get parser from abstract class
    # def get_name_related(self,model, name, value):
    #     message_ids = []
    #     res = []
    #     message_obj = self.pool.get('mail.message')
    #     # self.cr.execute('select from ',(b_line_ids,))
    #     budget_ids = self.cr.fetchall()
    #
    #     field = self.pool.get(model)._fields[name]
    #     env = api.Environment(self.cr, self.uid, self.localcontext)
    #     val = dict(field.get_description(env)['model'])[value]
    #     return self._translate(val)
    #
    #
    #     #
    #     # message_id = message_obj.search(self.cr, self.uid, [('model', '=','purchase.request'),
    #     #                                              ],)
    #     # tracking_obj = self.pool.get('mail.tracking.value')
    #     # # note: search return ids, browse return instances
    #     # ids = tracking_obj.search(self.cr, self.uid, [('mail_message_id', '=',ids),
    #     #                                              ],)
    #     # res = tracking_obj.browse(self.cr, self.uid, ids)
    #     # return message_id

class wrapped_report_purchase_request(osv.AbstractModel):
    _name = 'report.purchase_indonesia.report_purchase_request'
    _inherit = 'report.abstract_report'
    _template = 'purchase_indonesia.report_purchase_request'
    _wrapped_report_class = purchase_request_run_report
