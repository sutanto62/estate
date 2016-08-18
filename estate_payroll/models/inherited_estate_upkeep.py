# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
from datetime import datetime

class Upkeep(models.Model):
    """Extend Upkeep class to process payslip
    """
    _inherit = 'estate.upkeep'

    @api.multi
    def payslip_upkeep(self, ids):
        """
        Set upkeep, activity, labour, material and fingerprint state to payslip.
        :param ids: upkeep ids
        :return:
        """
        self.env['estate.upkeep'].search([('id', 'in', ids)]).write({'state': 'payslip'})
        self.env['estate.upkeep.activity'].search([('upkeep_id', 'in', ids)]).write({'state': 'payslip'})
        self.env['estate.upkeep.labour'].search([('upkeep_id', 'in', ids)]).write({'state': 'payslip'})
        self.env['estate.upkeep.material'].search([('upkeep_id', 'in', ids)]).write({'state': 'payslip'})

        return True

    @api.multi
    def approved_upkeep(self, ids):
        """
        Set upkeep, activity, labour, material and fingerprint state to approved (except fingerprint draft)
        :param ids: upkeep ids
        :return:
        """
        self.env['estate.upkeep'].search([('id', '=', ids)]).write({'state': 'approved'})
        self.env['estate.upkeep.activity'].search([('upkeep_id', 'in', ids)]).write({'state': 'approved'})
        self.env['estate.upkeep.labour'].search([('upkeep_id', 'in', ids)]).write({'state': 'approved'})
        self.env['estate.upkeep.material'].search([('upkeep_id', 'in', ids)]).write({'state': 'approved'})

        return True

    @api.multi
    def get_upkeep_by_employee(self, employees, start, end, state):
        """
        Search upkeep id based on employee and period
        :param employees: list of employee object
        :param start: date start
        :param end: date end
        :return: list of upkeep id
        """
        upkeeps = self.env['estate.upkeep'].search([('state', '=', state),
                                                    ('date', '>=', start),
                                                    ('date', '<=', end),
                                                    ('labour_line_ids.employee_id', 'in', employees)]).ids
        return upkeeps

class UpkeepLabour(models.Model):
    _inherit = 'estate.upkeep.labour'

    @api.multi
    def get_worked_days(self, ids):
        """
        Number of worked days required by salary rules
        :param ids: upkeep id
        :return:
        """
        number_of_days = 0

        for record in self.env['estate.upkeep.labour'].search([('id', 'in', ids)]):
            number_of_days += record['number_of_day']
        return number_of_days

    @api.multi
    def get_overtime(self, ids):
        """
        Number of overtime hours required by salary rules
        :param ids: upkeep labour
        :return:
        """
        overtime = 0.00

        for record in self.env['estate.upkeep.labour'].search([('id', 'in', ids)]):
            overtime += record['quantity_overtime']
        return overtime

    @api.multi
    def get_piece_rate(self, ids):
        """
        Amount of piece rate required by salary rules
        :param ids: upkeep labour
        :return: amount of piece rate
        """
        amount = 0.00

        for record in self.env['estate.upkeep.labour'].search([('id', 'in', ids)]):
            amount += record['wage_piece_rate']
        return amount

    @api.multi
    def get_workhour(self, ids):
        """
        Number of hours might be required by salary rules
        :param ids: upkeep labour
        :return: number of hours
        """
        workhour = 0.00
        att_obj = self.env['estate.hr.attendance']
        for record in self.env['estate.upkeep.labour'].search([('id', 'in', ids)]):
            att_code_id = record['attendance_code_id']['id']
            att_hour = att_obj.search([('id', '=', att_code_id)]).unit_amount
            hour = record['number_of_day'] * att_hour
            workhour += hour
        return workhour

    @api.multi
    def get_wage_number_of_day(self, ids):
        """
        Amount of piece rate required by salary rules
        :param ids: upkeep labour
        :return: wage number of day
        """
        amount = 0.00

        for record in self.env['estate.upkeep.labour'].search([('id', 'in', ids)]):
            amount += record['wage_number_of_day']
        return amount

    @api.multi
    def get_wage_overtime(self, ids):
        """
        Amount of piece rate required by salary rules
        :param ids: upkeep labour
        :return: wage overtime
        """
        amount = 0.00

        for record in self.env['estate.upkeep.labour'].search([('id', 'in', ids)]):
            amount += record['wage_overtime']
        return amount

    @api.multi
    def get_wage_piece_rate(self, ids):
        """
        Amount of piece rate required by salary rules
        :param ids: upkeep labour
        :return: wage piece rate
        """
        amount = 0.00

        for record in self.env['estate.upkeep.labour'].search([('id', 'in', ids)]):
            amount += record['wage_piece_rate']
        return amount