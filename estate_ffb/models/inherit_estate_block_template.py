# -*- coding: utf-8 -*-

from openerp import models, fields, api

class InheritEstateBlockTemplate(models.Model):
    _inherit = 'estate.block.template'

    estate_location_level = fields.Selection([('1', 'Estate'), ('2', 'Division'), ('3', 'Block'), ('4', 'Sub Block'),
                                              ('5', 'Ancak'), ('6', 'TPH')], string="Estate Location Level")