# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv, exceptions

class PayslipEmployee(models.Model):
    _inherit = 'hr.payslip.employees'

    @api.multi
    def get_upkeep(self):
        """Create payslip run. Payslip run based on parameters below:
        1. Date start and end (mandatory).
        2. Estate (optional or mandatory if division selected).
        3. Division (optional).
        :return:
        """
        # print 'Start get active labour with context %s' % self._context

        # Get payslip run date start and end
        payslip_run = self.env['hr.payslip.run'].search([('id', '=', self._context['active_id'])])

        # Get upkeep labour
        domain = [('state', '=', 'approved'),
                  ('upkeep_date', '>=', payslip_run.date_start),
                  ('upkeep_date', '<=', payslip_run.date_end)]
        if payslip_run.estate_id:
            domain.append(('estate_id', '=', payslip_run.estate_id.id))
        elif payslip_run.estate_id and payslip_run.division_id:
            domain.append(('estate_id', '=', payslip_run.estate_id.id),
                           ('division_id', '=', payslip_run.division_id.id))

        # Get labour
        labour = []
        payslip_labour = []
        employee_list = []
        upkeeps = []
        upkeep_list = []

        # Labour from upkeep
        for record in self.env['estate.upkeep.labour'].search(domain):
            labour.append(record.employee_id.id)
            upkeeps.append(record.upkeep_id.id)
        labour = set(labour)


        # Labour already at payslip
        for payslip in payslip_run.slip_ids:
            payslip_labour.append(payslip.employee_id.id)

        # Validation for double payslip
        labour = list(set(labour) - set(payslip_labour))

        upkeeps = set(upkeeps)

        for rec in labour:
            employee_list.append(rec)

        self.employee_ids = employee_list

        for rec_upkeep in upkeeps:
            upkeep_list.append(rec_upkeep)

        # Generate payslip and change upkeep state
        if not len(employee_list):
            error_msg = "No labour for selected period/division/estate."
            raise exceptions.ValidationError(error_msg)
        else:
            # Set payslip processed at close_payslip_run
            # self.env['estate.upkeep'].set_payslip_processed(upkeep_list)
            return super(PayslipEmployee, self).compute_sheet()

