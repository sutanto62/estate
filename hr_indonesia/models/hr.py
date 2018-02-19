# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.exceptions import ValidationError, RedirectWarning
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

import logging

_logger = logging.getLogger(__name__)

class Search(models.TransientModel):
    _name = 'hr_indonesia.search'
    _description = 'HR Indonesia Search'

    def check_archived(self, ids, object, attr, name=None, active=False, ):
        """
        Encapsulate search archived recordset
        :param object: self.env[]
        :type: object
        :param attr: model attribute
        :type: string
        :param active: False, search for archived. True, search for active record
        :param name: value
        :type: string
        :return: dict
        :rtype: boolean
        """
        res = object.search([('id', '!=', ids), ('active', '=', active)]).mapped(attr)
        return res


class Employee(models.Model):
    """Extend HR Employee to accommodate Indonesian Workforce.
    1. KHL is Daily PKWT.
    2. KHT is Daily PKWTT.
    3. Employee or Staf is Monthly PKWTT.
    4. Contract is Monthly PKWT.
    """
    _inherit = 'hr.employee'

    # Employee Information
    nik_number = fields.Char("Employee Identity Number", track_visibility="onchange")
    bpjs_number = fields.Char("BPJS Number")
    health_insurance_number = fields.Char("Health Insurance Number")
    npwp_number = fields.Char("NPWP Number")
    company_id = fields.Many2one('res.company', "Company", track_visibility="onchange")
    contract_type = fields.Selection([('1', 'PKWTT'), ('2', 'PKWT')], "Contract Type",
                                       help="* PKWTT, Perjanjian Kerja Waktu Tidak Tertentu, "\
                                            "* PKWT, Perjanjian Kerja Waktu Tertentu.", track_visibility="onchange")
    contract_period = fields.Selection([('1', 'Monthly'), ('2', 'Daily')], "Contract Period",
                                       help="* Monthly, Karyawan Bulanan, "\
                                            "* Daily, Karyawan Harian.", track_visibility="onchange")
    outsource = fields.Boolean("Outsource employee", help="Activate to represent employee as Outsource.")
    internship = fields.Boolean("Internship", help="Activate to represent internship employee.")
    age = fields.Float("Employee Age", compute='_compute_age')
    joindate = fields.Date("Date of Join", track_visibility='onchange')
    resigndate = fields.Date("Date of Resign", track_visibility='onchange')
    religion_id = fields.Many2one('hr_indonesia.religion', "Religion")
    ethnic_id = fields.Many2one('hr_indonesia.ethnic', "Ethnic")
    tax_marital_id = fields.Many2one('hr_indonesia.tax_marital', 'Tax Marital')
    tax_dependent = fields.Integer('Dependent')
    location_id = fields.Many2one('hr_indonesia.location', 'Placement Location')
    office_level_id = fields.Many2one('hr_indonesia.office', 'Office Level')
    supervisor_level_id = fields.Many2one('hr_indonesia.supervisor', 'Supervisor Level')
    #
    # point_of_hire_id = fields.Many2one('hr_indonesia.location', 'Point of Hire')
    # supervisorlevel_id = fields.Many2one('hr_indonesia.supervisor', 'Supervisor Level')


    def _compute_age(self):
        for record in self:
            record.age = 1

    def _check_nik(self, employee):
        """
        Daily employee's NIK has sequences related to company
        Args:
            employee:

        Returns:
            True if employee was not daily or employee company is equal to nik_number company
            False if employee was daily and employee company is not equal to nik_number company
        """
        # Only employee that contract period is daily
        if not employee.contract_period == '2':
            return True

        seq_obj = self.env['ir.sequence']
        nik_prefix = employee.nik_number[0:3]

        # make sure return singleton
        sequence_id = seq_obj.search([('prefix', 'like', '%' + nik_prefix),
                                      ('company_id', '=', employee.company_id.id)], limit=1)

        if employee.company_id == sequence_id.company_id:
            return True
        else:
            return False

    @api.multi
    @api.constrains('nik_number', 'identification_id')
    def _check_employee(self):
        """
        Required to check duplicate NIK (and format) or ID
        Returns: True if no duplicate found
        """

        for record in self:

            if record.nik_number:
                # find duplicate nik
                employee_ids = self.search([('id', 'not in', self.ids), ('nik_number', '=', record.nik_number)])
                if employee_ids:
                    error_msg = _("There is duplicate of Employee Identity Number.")
                    raise ValidationError(error_msg)

                # check nik format. it required base_indonesia
                if not record._check_nik(record):
                    error_msg = _("NIK did not match with Company Code.")
                    raise ValidationError(error_msg)

            if record.identification_id:
                employee_ids = self.search([('id', 'not in', self.ids), ('identification_id', '=', record.identification_id)])
                if employee_ids:
                    error_msg = _("There is duplicate of Identification Number.")
                    raise ValidationError(error_msg)

            return True

    @api.multi
    @api.constrains('resigndate')
    def _check_resigndate(self):
        """ Support scheduled resign date."""

        for employee in self:
            if employee.joindate and (employee.resigndate < employee.joindate):
                err_msg = _('%s resign date should not early than %s' % (employee.name, employee.joindate))
                raise ValidationError(err_msg)
            elif not employee.joindate:
                err_msg = _('Set join date before define resign date.')
                raise ValidationError(err_msg)
            else:
                return True

    @api.multi
    def toggle_active(self):
        """ Prevent archived without resign date. It archived active related contract."""
        limit = (datetime.today() + relativedelta(months=2, day=1)).strftime(DF)

        for employee in self:
            # archive only active employee with resign date, no vice versa
            if not employee.resigndate and employee.active:
                err_msg = _('Unable to archive employee without resign date.')
                raise ValidationError(err_msg)

            # archive after month+1
            if employee.resigndate < limit:
                err_msg = _('Unable to archive employee as next month payroll process.')
                raise ValidationError(err_msg)


            # cascaded to active contract only. unarchived employee did not make contract
            if employee.active:
                contract_ids = self.env['hr.contract'].search([('employee_id', '=', employee.id),
                                                               ('active', '=', True)])
                contract_ids.write({'active': False})

            super(Employee, employee).toggle_active()

    @api.multi
    def generate_nik(self, vals):
        """ Create NIK as corporate policy
        ir_sequence_code_1 = PKWTT/PKWT Monthly/PKWT Daily
        ir_sequence_code_2 = Estate
        """

        seq_obj = self.env['ir.sequence']
        res = ''

        # Internship and outsource has no Employee Identification Number
        if vals.get('internship') or vals.get('outsource'):
            return

        if vals.get('contract_type') == '1':
            # PKWTT Monthly/Daily
            res = seq_obj.with_context(ir_sequence_code_1='1').next_by_code('hr_indonesia.nik')
        elif vals.get('contract_type') == '2' and vals.get('contract_period') == '1':
            # Contract / PKWT Montly
            res = seq_obj.with_context(ir_sequence_code_1='2').next_by_code('hr_indonesia.nik_pkwt_monthly')
        else:
            return
        return res

    @api.model
    def create(self, vals):
        """ Avoid skipped number for standard sequence."""
        if not vals.get('nik_number'):
            vals['nik_number'] = self.generate_nik(vals)
        return super(Employee, self).create(vals)

    @api.multi
    def write(self, vals):
        """ Update Employee Identity automatically if there is changes at contract type or period."""

        for record in self:
            employee_id = record.env['hr.employee'].browse(record.id)

            change_type = change_period = False

            if vals.get('contract_type'):
                change_type = True if vals['contract_type'] != employee_id.contract_type else False

            if vals.get('contract_period'):
                change_period = True if vals['contract_period'] != employee_id.contract_period else False

            if change_type or change_period:
                # _generate_nik parameter is vals
                new_vals = {
                    'company_id': record.company_id.id,
                    # 'estate_id': record.estate_id.id, extend at estate module
                    'contract_type': vals['contract_type'] if 'contract_type' in vals else record.contract_type,
                    'contract_period': vals['contract_period'] if 'contract_period' in vals else record.contract_period,
                    # 'nik_number': record.nik_number,
                    'internship': record.internship,
                    'outsource': record.outsource
                }

                vals['nik_number'] = self.generate_nik(new_vals)
                _logger.info(_('Employee %s has new Employee Identity Number %s: ' % (employee_id.name, vals['nik_number'])))
            return super(Employee, self).write(vals)


class Religion(models.Model):
    """ Required to define THR allowance """
    _name = 'hr_indonesia.religion'
    _description = 'Religion'
    _inherit = 'mail.thread'

    name = fields.Char("Religion", track_visibility="onchange")
    sequence = fields.Integer('Sequence')
    active = fields.Boolean('Active', default=True)

    @api.constrains('name')
    def _check_name(self):
        obj = self.env['hr_indonesia.religion']
        search = self.env['hr_indonesia.search']

        if self.name.lower() in map(lambda x: x.lower(), search.check_archived(self.ids, obj, 'name', self.name)):
            err_msg = _('We found religion %s in archived record.\n'
                        'Please activate that record instead of create new one.' % self.name)
            raise ValidationError(err_msg)
        elif self.name.lower() in map(lambda x: x.lower(),
                                      search.check_archived(self.ids, obj, 'name', self.name, True)):
            err_msg = _('Religion %s is exist.' % self.name)
            raise ValidationError(err_msg)
        else:
            return True

    @api.multi
    def contract(self):
        """ Get current active contract."""
        return self.env['hr.contract'].current(self)



class Ethnic(models.Model):
    _name = 'hr_indonesia.ethnic'
    _description = 'Ethnic'
    _order = 'sequence'
    _inherit = 'mail.thread'

    name = fields.Char('Ethnic', track_visibility="onchange")
    sequence = fields.Integer('Sequence')
    active = fields.Boolean('Active', default=True)

    @api.constrains('name')
    def _check_name(self):
        """ No duplicate even for archived one."""
        obj = self.env['hr_indonesia.ethnic']
        search = self.env['hr_indonesia.search']

        if self.name.lower() in map(lambda x: x.lower(), search.check_archived(self.ids, obj, 'name', self.name)):
            err_msg = _('We found ethnic %s in archived record.\n'
                        'Please activate that record instead of create new one.' % self.name)
            raise ValidationError(err_msg)
        elif self.name.lower() in map(lambda x: x.lower(), search.check_archived(self.ids, obj, 'name', self.name, True)):
            err_msg = _('Ethnic %s is exist.' % self.name)
            raise ValidationError(err_msg)
        else:
            return True

class TaxMarital(models.Model):
    _name = 'hr_indonesia.tax_marital'
    _description = 'Tax Marital'
    _order = 'sequence'
    _inherit = 'mail.thread'

    name = fields.Char('Tax Marital', track_visibility="onchange")
    code = fields.Char('Code', help='Displayed at report.', track_visibility="onchange")
    sequence = fields.Integer('Sequence')
    active = fields.Boolean('Active', default=True)

    @api.constrains('name')
    def _check_name(self):
        """ No duplicate even for archived one."""
        obj = self.env['hr_indonesia.tax_marital']
        search = self.env['hr_indonesia.search']

        if self.name.lower() in map(lambda x: x.lower(), search.check_archived(self.ids, obj, 'name', self.name)):
            err_msg = _('We found tax marital %s in archived record.\n'
                        'Please activate that record instead of create new one.' % self.name)
            raise ValidationError(err_msg)
        elif self.name.lower() in map(lambda x: x.lower(),
                                      search.check_archived(self.ids, obj, 'name', self.name, True)):
            err_msg = _('Tax marital %s is exist.' % self.name)
            raise ValidationError(err_msg)
        else:
            return True


class Location(models.Model):
    """ Do not used stock location.
    """
    _name = 'hr_indonesia.location'
    _parent_store = True
    _parent_name = 'parent_id'
    _order = 'complete_name'
    _rec_name = 'name'  # complete_name too long for upkeep entry
    _inherit = ['mail.thread', 'hr_indonesia.search']

    _description = 'Placement Location'

    name = fields.Char('Location Name', required=True, track_visibility="onchange")
    complete_name = fields.Char("Complete Name", compute="_complete_name", store=True)
    code = fields.Char('Code', help='Write location abbreviation', track_visibility="onchange")
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
    active = fields.Boolean('Active', default=True)

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

    @api.constrains('name')
    def _check_name(self):
        """ No duplicate even for archived one."""
        obj = self.env['hr_indonesia.location']
        search = self.env['hr_indonesia.search']

        if self.name.lower() in map(lambda x: x.lower(), search.check_archived(self.ids, obj, 'name', self.name)):
            err_msg = _('We found location %s in archived record.\n'
                        'Please activate that record instead of create new one.' % self.name)
            raise ValidationError(err_msg)
        elif self.name.lower() in map(lambda x: x.lower(), search.check_archived(self.ids, obj, 'name', self.name, True)):
            err_msg = _('Location %s is exist.' % self.name)
            raise ValidationError(err_msg)
        else:
            return True


class Office(models.Model):
    """ Hierarchy of office - required by purchase"""
    _name = 'hr_indonesia.office'
    _parent_store = True
    _parent_name = 'parent_id'
    _order = 'sequence'
    _description = 'Office Level'
    _inherit = 'mail.thread'

    name = fields.Char('Name', required=True, track_visibility="onchange")
    code = fields.Char('Code', help='Write office level', track_visibility="onchange")
    comment = fields.Text("Additional Information")
    sequence = fields.Integer("Sequence", help="Small number higher position.")
    parent_id = fields.Many2one('hr_indonesia.office', "Parent Office", ondelete='restrict')
    parent_left = fields.Integer("Parent Left", index=True)
    parent_right = fields.Integer("Parent Right", index=True)
    child_ids = fields.One2many('hr_indonesia.office', 'parent_id', "Child Office Levels")
    active = fields.Boolean('Active', default=True)

    @api.constrains('name')
    def _check_name(self):
        obj = self.env['hr_indonesia.office']
        search = self.env['hr_indonesia.search']

        if self.name.lower() in map(lambda x: x.lower(), search.check_archived(self.ids, obj, 'name', self.name)):
            err_msg = _('We found office %s in archived record.\n'
                        'Please activate that record instead of create new one.' % self.name)
            raise ValidationError(err_msg)
        elif self.name.lower() in map(lambda x: x.lower(),
                                      search.check_archived(self.ids, obj, 'name', self.name, True)):
            err_msg = _('Office %s is exist.' % self.name)
            raise ValidationError(err_msg)
        else:
            return True


class SupervisorLevel(models.Model):
    """ Class of position such as Division Manager and Section Chief"""

    _name = 'hr_indonesia.supervisor'
    _parent_store = True
    _parent_name = 'parent_id'
    _order = 'sequence'
    _inherit = 'mail.thread'

    _description = 'Supervisor Level'

    name = fields.Char('Name', required=True, track_visibility="onchange")
    code = fields.Char('Code', help='Write supervisor level', track_visibility="onchange")
    comment = fields.Text("Additional Information")
    sequence = fields.Integer("Sequence", help="Small number higher position.")
    parent_id = fields.Many2one('hr_indonesia.supervisor', "Parent Supervisor", ondelete='restrict')
    parent_left = fields.Integer("Parent Left", index=True)
    parent_right = fields.Integer("Parent Right", index=True)
    child_ids = fields.One2many('hr_indonesia.supervisor', 'parent_id', "Child Supervisor Levels")
    active = fields.Boolean('Active', default=True)

    @api.constrains('code')
    def _check_code(self):
        """Code max 3"""
        if self.code:
            if len(self.code) > 3:
                msg_error = _('Supervisor level code should be 3 character long or less.')
                raise ValidationError(msg_error)
        else:
            return True

    @api.constrains('name')
    def _check_name(self):
        obj = self.env['hr_indonesia.supervisor']
        search = self.env['hr_indonesia.search']

        if self.name.lower() in map(lambda x: x.lower(), search.check_archived(self.ids, obj, 'name', self.name)):
            err_msg = _('We found supervisor level %s in archived record.\n'
                        'Please activate that record instead of create new one.' % self.name)
            raise ValidationError(err_msg)
        elif self.name.lower() in map(lambda x: x.lower(),
                                      search.check_archived(self.ids, obj, 'name', self.name, True)):
            err_msg = _('Supervisor level %s is exist.' % self.name)
            raise ValidationError(err_msg)
        else:
            return True