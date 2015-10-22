# -*- coding: utf-8 -*-

from openerp import models, fields

class EstateConfigSettings(models.TransientModel):
    _name = 'estate.config.settings'
    _inherit = 'res.config.settings'

    module_estate_nursery = fields.Boolean("Seed Management",
                                           help="Record receiving from purchase order, planting and selection.",
                                           default_model='estate.config.settings')