# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

class Employee(models.Model):
    """Extend HR Employee.
    """
    _inherit = 'hr.employee'

    estate_id = fields.Many2one('estate.block.template', 'Estate', help='Help to define NIK for estate labour',
                                domain=[('estate_location', '=', True), ('estate_location_level', '=', '1')])

