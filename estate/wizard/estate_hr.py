# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import openerp.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError, UserError

class WizardTeamMember(models.TransientModel):
    _name = 'estate.hr.member.wizard'
    _description = 'Move Team Member'

    team_id = fields.Many2one('estate.hr.team', 'Target Team', help='Choose target team.')

    @api.multi
    def move_team_member(self):
        """ Labour rotation."""
        member_ids = self.env['estate.hr.member'].browse(self._context['active_ids'])
        for member in member_ids:
            if not member.current_labour():
                if member.team_id == self.team_id:
                    err_msg = _('%s is already at the %s team.' % (member.employee_id.name,
                                                                               self.team_id.name))
                    raise UserError(err_msg)
                else:
                    member.move(self.team_id)
            else:
                err_msg = _('You should not move %s to %s.\n'
                            'Moving team member only if there is no upkeep record.' % (member.employee_id.name, self.team_id.name))
                raise UserError(err_msg)
        return True

