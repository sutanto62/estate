# -*- coding: utf-8 -*-

from openerp import models, fields, api
from rule_attendance import *

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

    @api.multi
    def get_worked_days(self, ids):
        """
        Override estate_upkeep from estate payroll module.
        Number of worked days which has attendance required by salary rules
        :param ids: upkeep id
        :return:
        """
        number_of_days = 0
        att_obj = self.env['hr.attendance']

        for record in self.env['estate.upkeep.labour'].search([('id', 'in', ids)]):
            res = UpkeepFingerprint(att_obj.get_attendance(record.employee_id, record.upkeep_date, 'sign_in'),
                                    att_obj.get_attendance(record.employee_id, record.upkeep_date, 'sign_out'),
                                    record.attendance_code_id)

            att_rule = UpkeepFingerprintSpecification().\
                and_specification(SignInSpecification()).\
                and_specification(SignOutSpecification()).\
                and_specification(AttendanceCodeSpecification())

            if att_rule.is_satisfied_by(res):
                number_of_days += record['number_of_day']
        return number_of_days
