from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import models, fields, api
from	openerp	import	exceptions

class RequestTransfer(models.TransientModel):
    # _name = 'estate.nursery.reqwiz'
    _inherit = 'stock.transfer_details'

    # name=fields.Char("Wizard name",related='request_id.bpb_code')
    # request_id=fields.Many2one('estate.nursery.request',)
    # requestline_ids = fields.One2many("","wizard_id")

    # def _get_request_id(self,cr,uid,ids,context):
    #     if context.get('active_model')== 'estate.nursery.request':
    #         return context.get('active_id',False)
    #     return False
    #
    # def action_add_wizard(self,cr,uid,ids,context=None):
    #    session_model= self.pool.get('academic_session')
    #    wizard=self.browse(cr,uid,ids[0],context=context)
    #    session_ids=(wizard.session_id.id)
    #    attData=[{'partner_id' : att.partner_id.id} for att in wizard.attendance_ids]
    #    session_model.write(cr,uid,session_ids,{'attendance_ids' : [(0,0,data) for data in attData]},context)
    #    return {}
    #
    # _defaults = {
    #     'request_id' : _get_request_id,
    #     'requestline_ids': lambda self, cr, uid, context : self.get_requestline_ids(cr, uid, [0], '', '', context)[0],
    # }
    @api.one
    def do_detailed_transfer(self):
        """
        Extend stock transfer wizard to create stock move and lot.
        """
        date_done = self.picking_id.date_done

        # Iterate through transfer detail item
        for item in self.item_ids:
            if item.product_id.seed:
                if date_done or item.variety_id or item.progeny_id:
                    lot_new = self.do_create_lot(item.product_id)
                    item.write({'lot_id': lot_new[0].id})
                    planting = self.do_create_plant(item, self, lot_new[0])
                    # self.do_create_plantline(item, planting[0])
                else:
                    raise exceptions.Warning('Required Date of Transfer, Variety and Progeny.')
            super(RequestTransfer, self).do_detailed_transfer()

        return True
    @api.one
    def do_create_lot(self, product):
        serial = self.env['estate.nursery.planting'].search_count([]) + 1

        lot_data = {
            'name': "planting %d" % serial,
            'product_id': product.id
        }

        return self.env['stock.production.lot'].create(lot_data)
    @api.one
    def do_create_planting(self, item, transfer, lot):
        """Create Lot and Seed Batch per transfer item."""
        date_done = transfer.picking_id.date_done
        # partner = transfer.picking_id.partner_id
        # product = item.product_id

        serial = self.env['estate.nursery.planting'].search_count([]) + 1

        # Validate Picking Date of Transfer
        if not date_done:
            raise exceptions.Warning('Press Cancel button and fill in date of transfer at Additional Info Tab.')

        plant_data = {
            'name': "planting %d" % serial,
            'lot_id': lot.id,
            'variety_id': item.variety_id.id,
            'date_received': date_done,
            'age_seed': transfer.age_seed,
            'qty_receive': item.quantity,
            'picking_id': transfer.picking_id.id,
            'estate_location_id':transfer.estate_location_id.id,
            'divisi_location_id' : transfer.divisi_location_id.id,
            'state': 'draft'
        }

        return self.env['estate.nursery.planting'].create(plant_data)

class request_wizard_detail(models.TransientModel):
    _name='create.wizard'

    wizard_id=fields.Many2one("estate.nursery.rewiz")

