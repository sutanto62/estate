# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv, _
from openerp.exceptions import ValidationError


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
    location_id = fields.Many2one('hr_indonesia.location', 'Placement Location')

    def _compute_age(self):
        for record in self:
            record.age = 1

    # def _check_employee(self, vals):
    #     """Check employee by NIK or ID number"""
    #     print 'vals are %s' % vals
    #     domain = []
    #     employee_ids = []
    #
    #     if vals['nik_number']:
    #         domain = [('nik_number', '=', vals['nik_number'])]
    #     if vals['identification_id']:
    #         domain = [('identification_id', '=', vals['identification_id'])]
    #     if vals['nik_number'] and vals['identification_id']:
    #         domain = ['|', ('nik_number', '=', vals['nik_number']), ('identification_id', '=', vals['identification_id'])]
    #
    #     print domain
    #     if domain:
    #         employee_ids = self.search(domain)
    #         print employee_ids
    #
    #     if employee_ids:
    #         error_msg = "There have been employee with entered NIK and ID number."
    #         raise ValidationError(error_msg)
    #
    #     return True
    #
    # @api.model
    # def create(self, vals):
    #     self._check_employee(vals)
    #     return super(Employee, self).create(vals)

    @api.one
    @api.constrains('nik_number', 'identification_id')
    def _check_employee(self):
        """
        Required to check duplicate NIK or ID
        Returns: True if no duplicate found
        """
        for record in self:
            # put self.ids to exclude it self
            employee_ids = []
            if self.nik_number or self.identification_id:
                employee_ids = self.search([('id', 'not in', self.ids),
                                            '|',
                                            ('nik_number', '=', record.nik_number),
                                            ('identification_id', '=', record.identification_id)])

            if employee_ids:
                error_msg = "There is duplicate of Employee Identity Number or Identification No."
                raise ValidationError(error_msg)

            return True


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


class Location(models.Model):
    """ Do not used stock location.
    """
    _name = 'hr_indonesia.location'
    _parent_store = True
    _parent_name = 'parent_id'
    _order = 'complete_name'
    _rec_name = 'name'  # complete_name too long for upkeep entry

    _description = 'Placement Location'

    name = fields.Char('Location Name', required=True)
    complete_name = fields.Char("Complete Name", compute="_complete_name", store=True)
    code = fields.Char('Code', help='Write location abbreviation')
    type = fields.Selection([('view', "View"),
                             ('normal', "Normal")], "Type",
                            required=True,
                            help="Select View to create group of location.")
    comment = fields.Text("Additional Information")
    sequence = fields.Integer("Sequence", help="Keep location in order.") # todo set as parent_left at create
    parent_id = fields.Many2one('hr_indonesia.location', "Parent Category", ondelete='restrict')
    parent_left = fields.Integer("Parent Left",	index=True)
    parent_right = fields.Integer("Parent Right", index=True)
    child_ids = fields.One2many('hr_indonesia.location', 'parent_id', "Child Locations")

    @api.multi
    @api.depends('name', 'parent_id')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        for record in self:
            if record.parent_id:
                record.complete_name = record.parent_id.complete_name + ' / ' + record.name
            else:
                record.complete_name = record.name