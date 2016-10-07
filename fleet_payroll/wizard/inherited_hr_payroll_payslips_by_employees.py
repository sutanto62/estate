from openerp import models, fields, api, osv, exceptions

class PayslipEmployee(models.Model):

    _inherit = 'hr.payslip.employees'

    @api.multi
    def get_fleet_employee(self):

        payslip_run = self.env['hr.payslip.run'].search([('id', '=', self._context['active_id'])])

        domain = [('date_activity_transport', '>=', payslip_run.date_start)]

        # Get labour
        labour = []
        payslip_labour = []
        employee_list = []


        # Labour from Timesheet
        for record in self.env['estate.timesheet.activity.transport'].search(domain):
            labour.append(record.employee_id.id)
        labour = set(labour)

        # Labour already at payslip
        for payslip in payslip_run.slip_ids:
            payslip_labour.append(payslip.employee_id.id)

        # Validation for double payslip
        labour = list(set(labour) - set(payslip_labour))


        for rec in labour:
            employee_list.append(rec)
        self.employee_ids = employee_list


        # Generate payslip and change upkeep state
        if not len(employee_list):
            error_msg = "No labour for selected period"
            raise exceptions.ValidationError(error_msg)
        else:
            # Set payslip processed at close_payslip_run
            return super(PayslipEmployee, self).compute_sheet()

