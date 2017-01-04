# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
import logging

from openerp.exceptions import ValidationError, RedirectWarning

_logger = logging.getLogger(__name__)


class Department(models.Model):
    """ Code required for sequence number at Purchase Request"""
    _inherit = 'hr.department'

    code = fields.Char('Department Code', help='Capital letters 3 characters long.')

    @api.multi
    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if record.code:
                if len(record.code) > 4:
                    msg_error = _('Maximum 4 characters long.')
                    raise ValueError(msg_error)