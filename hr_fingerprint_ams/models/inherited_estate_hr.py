# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime
import openerp.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from openerp.exceptions import ValidationError


class AttendanceCode(models.Model):
    """ Attendance policy might required complete or single in and out."""
    _inherit = 'estate.hr.attendance'

    fingerprint = fields.Selection([('complete', 'Complete'),
                                    ('single', 'Single')], 'Fingerprint Requirement',
                                   help='* Complete, employee with this attendance code should clock-in AND clock-out.\n'
                                        '* Single, employee with this attendance code allowed to have clock-in OR clock-out only.',
                                   default='complete')
