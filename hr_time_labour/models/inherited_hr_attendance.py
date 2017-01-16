# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

class ActionReason(models.Model):
    """
    Show action reason for action type Action. Default module forgot to include 'action' selection
    """
    _inherit = 'hr.action.reason'

    action_type = fields.Selection(selection_add=[('action', 'Action')])
    action_duration = fields.Float('Worked Hours', help="Define worked hours for non sign-in/out action type. Exclude break.")


class Attendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def create(self, vals):
        # cannot override _worked_hours_compute
        action_desc_id = self.env['hr.action.reason'].search([('id', '=', vals['action_desc'])])

        # sign-in/sign-out action do not use action_duration
        if self.action == 'action' and action_desc_id.action_duration:
            vals['worked_hours'] = action_desc_id.action_duration

        return super(Attendance, self).create(vals)

