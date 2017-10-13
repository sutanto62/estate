# -*- coding: utf-8 -*-

from openerp import models, fields, api

class RainfallConfigSettings(models.TransientModel):
    _inherit = 'estate.config.settings'

    default_time_start = fields.Float('Morning Observation Time Start', default=17.0,
                                      help='Morning observation used yesterday data, H-1.')
    default_time_end = fields.Float('Morning Observation Time End', default=6.0,
                                    help='Morning observation time end at current day, H\n')
    default_time_overnight = fields.Boolean('Observation time overnight', default=True,
                                            help='Set True if observation time start and end overnight.')
    default_observation_method = fields.Selection([('start', 'Based on start time'),
                                                   ('end', 'Based on end time')], 'How to define observation',
                                                  help='How to define observation', default='start')


