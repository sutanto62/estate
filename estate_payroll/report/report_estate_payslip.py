#-*- coding:utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv
from openerp.report import report_sxw
import math

class estate_payslip_run_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(estate_payslip_run_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_payslip': self.get_payslip,
            'get_team': self.get_team,
            'get_payslip_team': self.get_payslip_team,
            'get_overtime_employee': self.get_overtime_employee,
            'get_line_total': self.get_line_total,
            'get_payslip_total': self.get_payslip_total,
            'get_number_of_day': self.get_number_of_day,
            'number_round': self.number_round,
            'get_worked_day': self.get_worked_day,
            'get_division': self.get_division,
            # 'get_qrcode': self.get_qrcode,
            #'get_payslip_lines': self.get_payslip_lines,
        })

    def get_payslip(self, ids):
        res = []
        team = []
        payslip_line_obj = self.pool.get('hr.payslip')
        # team_obj = self.pool.get('estate.hr.team')
        for t in payslip_line_obj.browse(self.cr, self.uid, ids):
            team.append(t.team_id.name)

        res = set(team)
        return res

    def get_division(self, obj):
        """
        Report payslip by division
        Args:
            obj:

        Returns:
        list of division instances
        """
        division_ids = []
        res = []
        payslip_obj = self.pool.get('hr.payslip')
        division_obj = self.pool.get('stock.location')

        domain = [('state', 'in', ('draft', 'verify')),
                  ('date_from', '>=', obj.date_start),
                  ('date_to', '<=', obj.date_end),
                  ('payslip_run_id', '=', obj.id),
                  ('company_id', '=', obj.company_id.id)]

        if obj.division_id:
            domain.append(('division_id', '=', obj.division_id.id))

        ids = payslip_obj.search(self.cr, self.uid, domain)

        for record in payslip_obj.browse(self.cr, self.uid, ids):
            division_ids.append(record.division_id.id)

        division_ids = set(division_ids)

        # Get team instances
        if division_ids:
            res = division_obj.browse(self.cr, self.uid, division_ids)

        return sorted(res, key=lambda d: d.name)

    def get_team(self, obj, division=None):
        """
        Report payslip by team get from payslip.
        :param
            obj: Payslip Run.
            division: Upkeep Division.
        :return: list of team instances
        """
        team_ids = []
        res = []
        payslip_obj = self.pool.get('hr.payslip')
        team_obj = self.pool.get('estate.hr.team')

        # Get team
        domain = [('state', 'in', ('draft','verify')),
                  ('date_from', '>=', obj.date_start),
                  ('date_to', '<=', obj.date_end),
                  ('payslip_run_id', '=', obj.id),
                  ('company_id', '=', obj.company_id.id)]

        if division:
            domain.append(('division_id', '=', division.id))

        ids = payslip_obj.search(self.cr, self.uid, domain)

        for record in payslip_obj.browse(self.cr, self.uid, ids):
            team_ids.append(record.team_id.id)

        team_ids = set(team_ids)

        # Get team instances
        if team_ids:
            res = team_obj.browse(self.cr, self.uid, team_ids)
            
        return sorted(res, key=lambda d: d.name)

    def get_payslip_team(self, id, date_start, date_end, payslip_run_id, company_id):
        """
        Get payslip's estate worker at any state (xml report to filter state) at given period
        Args:
            id: team
            date_start: payroll batch start date
            date_end: payroll batch end date
            payslip_run_id: payslip run
        Returns: payslip instances
        """
        payslip_obj = self.pool.get('hr.payslip')

        # note: search return ids, browse return instances
        ids = payslip_obj.search(self.cr, self.uid, [('contract_type_id', '=', 'Estate Worker'),
                                                     ('team_id', '=', id),
                                                     ('date_from', '=', date_start),
                                                     ('date_to', '=', date_end),
                                                     ('payslip_run_id', '=', payslip_run_id),
                                                     ('company_id', '=', company_id)], order='employee_id')
        res = payslip_obj.browse(self.cr, self.uid, ids)
        return res

    def get_overtime_employee(self, id, start, end):
        """
        Get overtime unit of approved upkeep
        :param id: employee
        :param start: payslip run date start
        :param end: payslip run date end
        :return: unit of overtime
        """
        upkeep_labour_obj = self.pool.get('estate.upkeep.labour')
        upkeep_labour_ids = upkeep_labour_obj.search(self.cr, self.uid, [('employee_id', '=', id),
                                                                         ('upkeep_date', '>=', start),
                                                                         ('upkeep_date', '<=', end),
                                                                         ('state', '=', 'approved')])
        return sum(upkeep.quantity_overtime for upkeep in upkeep_labour_obj.browse(self.cr, self.uid, upkeep_labour_ids))


    def get_line_total(self, id, employee_id, code):
        """
        Get payslip line total amount
        :param id: payslip id
        :param employee_id: employee
        :param code: salary rule code (EDW,OT,PR)
        :return: total amount
        """
        line_obj = self.pool.get('hr.payslip.line')

        line_id = line_obj.search(self.cr, self.uid, [('slip_id', '=', id),
                                                      ('employee_id', '=', employee_id),
                                                      ('code', '=', code)])
        line = line_obj.browse(self.cr, self.uid, line_id)
        return line.total

    def get_payslip_total(self, obj):
        """
        Get payslip total amount
        :param obj: payslip lines
        :return: total amount
        """
        line_obj = self.pool.get('hr.payslip.line')
        line_ids = []
        for id in range(len(obj)):
            line_ids.append(obj[id].id)
        return sum(line.total for line in line_obj.browse(self.cr, self.uid, line_ids))

    def get_number_of_day(self, obj):
        """ Get ratio HK/Bulan"""
        return True

    def number_round(self, val, round):
        return float(math.ceil(val / round)) * round

    def get_worked_day(self, obj, code):
        """
            Get number of days based on code
        Args:
            obj: worked day collection
            code: salary rule code
        Returns:
        """
        worked_days_obj = self.pool.get('hr.payslip.worked_days')
        worked_days_ids = worked_days_obj.search(self.cr, self.uid, [('code', '=', code),
                                                                     ('id', 'in', obj.ids)])
        return sum(line.number_of_days for line in worked_days_obj.browse(self.cr, self.uid, worked_days_ids))

class wrapped_report_payslip(osv.AbstractModel):
    _name = 'report.estate_payroll.report_estate_payslip'
    _inherit = 'report.abstract_report'
    _template = 'estate_payroll.report_estate_payslip'
    _wrapped_report_class = estate_payslip_run_report

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
