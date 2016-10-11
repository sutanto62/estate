# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

class ActionReason(models.Model):
    """
    Show action reason for action type Action. Default module forgot to include 'action' selection
    """
    _inherit = 'hr.action.reason'

    action_type = fields.Selection(selection_add=[('action', 'Action')])
    action_duration = fields.Float('Worked Hours', help="Define worked hours for non sign-in/out action type")


class Attendance(models.Model):
    _inherit = 'hr.attendance'

    @api.multi
    def _worked_hours_compute(self):
        """
        Non Sign In/Out has no worked hours
        Returns:
        """
        for record in self:
            if record.action == 'action':
                print 'Set worked hours'
            else:
                return super(Attendance, self)._worked_hours_compute()


