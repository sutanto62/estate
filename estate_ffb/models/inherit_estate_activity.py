# -*- coding: utf-8 -*-

from openerp import models, fields, api

class InheritEstateActivity(models.Model):
    _inherit = 'estate.activity'

    activity_type = fields.Selection([('estate', 'Estate Upkeep'),
                                      ('vehicle', 'Vehicle activity'),
                                      ('general', 'General Affair Activity'),
                                      ('harvest', 'Estate Harvest')],
                                     'Activity Type')

class InheritEstateUpkeepActivity(models.Model):
    _inherit = 'estate.upkeep.activity'

    activity_id = fields.Many2one('estate.activity', 'Activity', domain=[('type', '=', 'normal'),
                                    ('activity_type', 'in', ('estate', 'harvest'))],
                                    track_visibility='onchange', help='Any update will reset Block.', required=True)
