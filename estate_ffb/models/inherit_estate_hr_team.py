# -*- coding: utf-8 -*-

from openerp import models, fields, api

class InheritEstateHrTeam(models.Model):
    _inherit = 'estate.hr.team'

    activity_type = fields.Selection([('estate', 'Estate Upkeep'),
                                      ('harvest', 'Estate Harvest')],
                                     'Activity Type')