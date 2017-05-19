# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv, _

class CompanyAccount(models.Model):
    """ Define bank account for payroll"""
    _name = 'estate_account.company_account'
    _description = 'Payroll Bank Account'
    _inherit = ['mail.thread']

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, track_visibility="onchange")
    debit_id = fields.Many2one('account.account', 'Payroll Debit Account', track_visibility="onchange",
                               help='Company received account.')
    credit_id = fields.Many2one('account.account', 'Payroll Credit Account', track_visibility="onchange",
                                help='Company transfer account.')
    # Company might have one or more payable account
    # payable_id = fields.Many2one('account.account', 'Payable Account', track_visibility="onchange",
    #                              domain=[('user_type_id.type', '=', 'payable'),
    #                                      ('company_id', '!=', company_id)])
    receivable_id = fields.Many2one('account.account', 'Receivable Account', track_visibility="onchange",
                                 domain=[('user_type_id.type', '=', 'receivable')])
    default = fields.Boolean('Default', help='Default Bank Account for all payroll.')

    # todo constraints single company account


class PayrollCostCategory(models.Model):
    _name = 'estate_account.payroll_cost_category'
    _description = 'Estate Payroll Cost Category'

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)
    code = fields.Char('Code')
    aggregation = fields.Text('SQL Syntax')
    comment = fields.Text('Additional Information')


class PayrollCost(models.Model):
    _name = 'estate_account.payroll_cost'
    _description = 'Estate Payroll Cost'
    _inherit = ['mail.thread']

    def compute_amount_python_code(self):
        return '''
        # Available variables:
#----------------------
# payslip: object containing the payslips
# employee: hr.employee object
# contract: hr.contract object
# rules: object containing the rules code (previously computed)
# categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
# worked_days: object containing the computed worked days.
# inputs: object containing the computed inputs.

# Note: returned value have to be set in the variable 'result'

result = contract.wage * 0.10
        '''

    name = fields.Char('Payroll Cost Name')
    active = fields.Boolean('Active', default=True)
    contract_type = fields.Selection([('1', 'PKWTT'), ('2', 'PKWT')], "Contract Type",
                                     required=True,
                                     help="* PKWTT, Perjanjian Kerja Waktu Tidak Tertentu, " \
                                          "* PKWT, Perjanjian Kerja Waktu Tertentu.", track_visibility="onchange")
    contract_period = fields.Selection([('1', 'Monthly'), ('2', 'Daily')], "Contract Period",
                                       required=True,
                                       help="* Monthly, Karyawan Bulanan, " \
                                            "* Daily, Karyawan Harian.", track_visibility="onchange")
    amount_python_compute = fields.Text('Python Code', default=compute_amount_python_code)
    category_id = fields.Many2one('estate_account.payroll_cost_category', 'Cost Category', required=True, help="Help to collect amount of wage.")
    account_id = fields.Many2one('account.account', 'General Account', required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True)

