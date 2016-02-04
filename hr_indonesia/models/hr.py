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
    npwp_number = fields.Char("NPWP Number")
    company_id = fields.Many2one('res.company', "Cost Center")
    contract_type = fields.Selection([('1', 'PKWTT'), ('2', 'PKWT')], "Contract Type",
                                       help="*PKWTT, Perjanjian Kerja Waktu Tidak Tertentu, "
                                            "*PKWT, Perjanjian Kerja Waktu Tertentu.")
    contract_period = fields.Selection([('1', 'Monthly'), ('2', 'Daily')], "Contract Period",
                                       help="*Monthly, Karyawan Bulanan, "
                                            "*Daily, Karyawan Harian.")
    outsource = fields.Boolean("Outsource employee", help="Activate to represent employee as Outsource.")
    internship = fields.Boolean("Internship", help="Activate to represent internship employee.")
