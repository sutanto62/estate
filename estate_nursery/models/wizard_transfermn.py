from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import	exceptions
from openerp import models, fields, api, exceptions
from openerp import workflow
from dateutil.relativedelta import *
import calendar

class TransferDetailMn(models.TransientModel):
    """Extend Transfer Detail to create Seed Batch."""
    _name="estate.transfermn.wizard"

    def _default_session(self):
        return self.env['estate.nursery.transfermn'].browse(self._context.get('active_id'))


    transfermn_id = fields.Many2one('estate.nursery.transfermn',
        string="Session", required=True, default=_default_session)

    name=fields.Char()
    batch_id=fields.Many2one('estate.nursery.batch')
    location_mn_id = fields.Many2one('estate.block.template', "Plot",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '3'),
                                          ('estate_location_type', '=', 'nursery'),
                                          ('stage_id','=',4),
                                          ('scrap_location', '=', False)],
                                  help="Fill in location seed planted.")
    qty_move = fields.Integer('Quantity to Move')

    location_pn_id = fields.Many2one('estate.block.template', "Bedengan",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '3'),
                                          ('estate_location_type', '=', 'nursery'),
                                          ('stage_id','=',3),
                                          ('scrap_location', '=', False)],
                                  help="Fill in location seed planted.")
    date_transfer = fields.Date('Date Transfer Mn',required=True)

    @api.one
    def do_detailed_transfermn(self):
        """
        Extend stock transfer wizard to create stock move and lot.
        """
        # Iterate through transfer detail item
        for item in self:
            if item.qty_move or item.location_pn_id:
                transfermn = self.do_create_transfermn(self)
                self.do_create_transfermnline(item,transfermn[0])
            else:
                raise exceptions.Warning('Required Date of Transfer, Variety and Progeny.')
            super(TransferDetailMn, self).do_detailed_transfermn()

        return True

    @api.one
    def do_create_transfermn(self):
        """Create Transfer Mn per transfer item."""

        serial = self.env['estate.nursery.transfermn'].search_count([]) + 1

        transfermn_data = {
            'name': "Transfer Mn %d" % serial,
            'batch_id': self.batch_id,
            'date_transfer': self.date_transfer,
            'location_mn_id': self.location_mn_id,
            'state': 'draft'
        }

        return self.env['estate.nursery.transfermn'].create(transfermn_data)

    @api.one
    def do_create_transfermnline(self):
        """Create Transfer line Mn per transfer item."""

        serial = self.env['estate.nursery.transfermnline'].search_count([]) + 1

        transfermnline_data = {
            'name': "Transfer Mn %d" % serial,
            'qty_move': self.qty_move,
            'location_pn_id':self.location_pn_id,
        }

        return self.env['estate.nursery.transfermnline'].create(transfermnline_data)