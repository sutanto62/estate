# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

from openerp import models, fields, api, exceptions

class bid_line_qty(models.TransientModel):
    _inherit = "bid.line.qty"
    _description = "Change Bid line quantity"

    def change_qty(self, cr, uid, ids, context=None):
        active_ids = context and context.get('active_ids', [])
        data = self.browse(cr, uid, ids, context=context)[0]
        self.pool.get('purchase.order.line').write(cr, uid, active_ids, {'quantity_tendered': data.qty,
                                                                         'trigger_state':True})
        return {'type': 'ir.actions.act_window_close'}
