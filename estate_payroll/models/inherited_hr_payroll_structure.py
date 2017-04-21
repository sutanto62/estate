# -*- coding: utf-8 -*-

from openerp import models, fields


class PayrollStructure(models.Model):

    _inherit = 'hr.salary.rule'

    bpjs = fields.Boolean('BPJS', help="Marked to appear at BPJS Report.")
