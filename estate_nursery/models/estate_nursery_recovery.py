from openerp import models, fields, api, exceptions, _
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar


class NurseryRecovery(models.Model):

    _name ="estate.nursery.recovery"

    name=fields.Char(related="selection_id.name")
    selection_id=fields.Many2one('estate.nursery.selection',"Batch")
    partner_id=fields.Many2one('res.partner')
    qty_recovery= fields.Integer("Quantity Recovery")
    culling_location_id = fields.Many2one('estate.block.template',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),
                                                  ('scrap_location', '=', True)]
                                          ,store=True,required=True)
    location_id = fields.Many2one('estate.block.template', "Bedengan",
                                    domain=[('estate_location', '=', True),
                                            ('estate_location_level', '=', '3'),
                                            ('estate_location_type', '=', 'nursery'),
                                            ('scrap_location', '=', False),
                                            ],
                                             help="Fill in location seed planted.",
                                             required=True,)

# class RecoveryLine(models.Model):
#
#     _name = "estate.nursery.recoveryLine"
#
#
#     name=fields.Char(related='recovery_id.name')
#     recovery_id=fields.Many2one('estate.nursery.recovery')



