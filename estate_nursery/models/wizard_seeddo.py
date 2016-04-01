# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import	exceptions
from openerp import models, fields, api, exceptions
from openerp import workflow

import	logging
_logger	=	logging.getLogger(__name__)

class TransferSeed(models.TransientModel):

    _name = 'estate.nursery.transfer'
    # _inherit = ['stock.transfer_details']

    date_transfer=fields.Date("Date Transfer")
    transferline_ids=fields.One2many("estate.nursery.transferline",'transfer_id','Detail Transfer')

    name=fields.Char()

    def act_cancel(self, cr, uid, ids, context=None):
        #self.unlink(cr, uid, ids, context)
        return {'type':'ir.actions.act_window_close' }

    # @api.multi
    # def transferSeed(self):

    # @api.one
    # def do_detailed_transfer(self):
    #     """
    #     Extend stock transfer wizard to create planting.
    #     """
    #     date_done = self.picking_id.date_done
    #
    #     # Iterate through transfer detail item
    #     for item in self.item_ids:
    #         if item.product_id.seed:
    #             if date_done or item.variety_id or item.progeny_id:
    #                 lot_new = self.do_create_lot(item.product_id)
    #                 item.write({'lot_id': lot_new[0].id})
    #                 batch = self.do_create_batch(item, self, lot_new[0])
    #                 self.do_create_batchline(item, batch[0])
    #             else:
    #                 raise exceptions.Warning('Required Date of Transfer, Variety and Progeny.')
    #         super(TransferSeed, self).do_detailed_transfer()
    #
    #     return True

class TransferSeedLine(models.TransientModel):

    _name="estate.nursery.transferline"

    def _default_session(self):
        return self.env['estate.nursery.seeddo'].browse(self._context.get('active_id'))

    seeddo_id = fields.Many2one('estate.nursery.seeddo',
        string="Session", required=True, default=_default_session)
    qty_request = fields.Integer("Quantity Request")
    transfer_id = fields.Many2one('estate.nursery.transfer')

    @api.one
    def get_qty_request(self):
        self.qty_request = 0
        if self.seeddo_id:
            for item in self.seeddo_id:
                self.qty_request += item.batch_planted_ids.total_qty_pokok

        return  True

class DetailTransferSeed(models.TransientModel):

    _inherit= "estate.nursery.transferline"

    qty_difference=fields.Integer('Quantity Difference',track_visibility='onchange')
    qty_result=fields.Integer('Quantity Result',track_visibility='onchange')


    #onchange field
    # @api.one
    # @api.onchange('qty_result','qty_difference','total_qty_pokok ')
    # def onchange_qty_result(self):
    #     if self.total_qty_pokok:
    #         self.qty_result = self.total_qty_pokok - self.qty_difference
    #         self.write({'qty_result' : self.qty_result})