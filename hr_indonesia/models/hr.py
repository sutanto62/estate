# -*- coding: utf-8 -*-

from openerp import models, fields

class Employee(models.Model):
    """Extend HR Employee to accommodate Indonesian Workforce.
    1. KHL is Daily PKWT.
    2. KHT is Daily PKWTT.
    3. Employee or Staf is Monthly PKWTT.
    4. Contract is Monthly PKWT.
    """
    _inherit = 'hr.employee'

    # Employee Information
    nik_number = fields.Char("Employee Identity Number")
    bpjs_number = fields.Char("BPJS Number")
    health_insurance_number = fields.Char("Health Insurance Number")
    npwp_number = fields.Char("NPWP Number")
    company_id = fields.Many2one('res.company', "Cost Center")
    contract_type = fields.Selection([('1', 'PKWTT'), ('2', 'PKWT')], "Contract Type",
                                       help="* PKWTT, Perjanjian Kerja Waktu Tidak Tertentu, "\
                                            "* PKWT, Perjanjian Kerja Waktu Tertentu.")
    contract_period = fields.Selection([('1', 'Monthly'), ('2', 'Daily')], "Contract Period",
                                       help="* Monthly, Karyawan Bulanan, "\
                                            "* Daily, Karyawan Harian.")
    outsource = fields.Boolean("Outsource employee", help="Activate to represent employee as Outsource.")
    internship = fields.Boolean("Internship", help="Activate to represent internship employee.")
    age = fields.Float("Employee Age", compute='_compute_age')
    joindate = fields.Date("Date of Join")
    religion_id = fields.Many2one('hr_indonesia.religion', "Religion")
    ethnic_id = fields.Many2one('hr_indonesia.ethnic', "Ethnic")
    tax_marital_id = fields.Many2one('hr_indonesia.tax_marital', 'Tax Marital')
    tax_dependent = fields.Integer('Dependent')

    def _compute_age(self):
        for record in self:
            record.age = 1


class Religion(models.Model):
    """ Required to define THR allowance """
    _name = 'hr_indonesia.religion'
    _description = 'Religion'

    name = fields.Char("Religion")
    sequence = fields.Integer('Sequence')


class Ethnic(models.Model):
    _name = 'hr_indonesia.ethnic'
    _description = 'Ethnic'

    name = fields.Char('Ethnic')
    sequence = fields.Integer('Sequence')


class TaxMarital(models.Model):
    _name = 'hr_indonesia.tax_marital'
    _description = 'Tax Marital'

    name = fields.Char('Tax Marital')
    code = fields.Char('Code', help='Displayed at report.')
    sequence = fields.Integer('Sequence')