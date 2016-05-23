# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv

class Team(models.Model):
    """Payroll location should be defined
    """

    _inherit = 'estate.hr.team'

    payroll_location_id = fields.Many2one('stock.location', "Payroll Location",
                                           domain=[('estate_location', '=', True),
                                                   ('estate_location_level', '=', '2')],
                                          help="Define location of payroll disbursement")
