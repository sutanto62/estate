# -*- coding: utf-8 -*-

from openerp import models, fields, api

class UpkeepLabour(models.Model):
    """
    Monitor hr attendance per upkeep labour.
    """
    _inherit = 'estate.upkeep.labour'

    attendance_in = fields.Many2one('hr.attendance', 'Sign In', compute='_compute_attendance')
    attendance_out = fields.Many2one('hr.attendance', 'Sign Out', compute='_compute_attendance')

    @api.one
    @api.depends('employee_id', 'upkeep_date')
    def _compute_attendance(self):
        att_obj = self.env['hr.attendance']
        if self.employee_id and self.upkeep_date:
            attendance_in_id = att_obj.get_attendance(self.employee_id, self.upkeep_date, 'sign_in')
            attendance_out_id = att_obj.get_attendance(self.employee_id, self.upkeep_date, 'sign_out')
            if attendance_in_id:
                self.attendance_in = attendance_in_id.id
            if attendance_out_id:
                self.attendance_out = attendance_out_id.id
