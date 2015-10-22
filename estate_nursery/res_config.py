# -*- coding: utf-8 -*-

from openerp import models, fields

class NurseryConfigSettings(models.TransientModel):
    _inherit = 'estate.config.settings'

    # use default_ to implements res.config.settings getter and setter
    default_nursery_stage = fields.Selection([
        ('1', 'Single Stage'),
        ('2', 'Double Stage'),
        ('3', 'No Stage')],
        "Default Nursery Stage",
        help="Select for default nursery stage.",
        default='1',
        default_model='estate.config.settings')