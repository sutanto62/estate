from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re


class InheritResPartner(models.Model):
    @api.multi
    def purchase_procurement_staff(self):
        return self.env.ref('purchase_request.group_purchase_request_procstaff', False).id

    @api.multi
    def _get_user(self):
        #find User
        user= self.env['res.users'].browse(self.env.uid)

        return user

    @api.multi
    def _get_employee_request(self):
        #find User Employee

        employee = self.env['hr.employee'].search([('user_id','=',self._get_user().id)])

        return employee

    _inherit = 'res.partner'

    _description = 'Inherit Res Partner'

    product_category_ids = fields.Many2many('product.category','supplier_product_category_rel','partner_id','categ_id',string='Category Product')
    partner_product = fields.Char('Partner Product')
    state = fields.Selection([('draft','Draft'),('done','Done'),('confirm','Confirm'),
                       ('reject','Reject')],default='draft')
    confirmed_by = fields.Many2one('res.users','Confirmed By')
    approved_by = fields.Many2one('res.users','Approved By')
    assign_to = fields.Many2one('res.users','Assign To')
    partner_code = fields.Char('Partner Code')
    partner_running_number = fields.Char('Partner Running Number',compute='_generate_running_number_vendor')
    businesspermit_ids = fields.One2many('base.indonesia.vendor.business.permit','partner_id')
    businessteaxes_ids = fields.One2many('base.indonesia.taxes','partner_id')
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip',size=24, change_default=True)
    city =fields.Char('City')
    state_id =fields.Many2one("res.country.state", 'State',ondelete='restrict')
    country_id = fields.Many2one('res.country', 'Country', ondelete='restrict')
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')


    @api.multi
    @api.depends('partner_code')
    def _generate_running_number_vendor(self):
        for item in self:

            name_substring = '' if not item.name else item.name
            substring_first_caracter = name_substring[:1]
            if item.partner_code:

                vendor_code = substring_first_caracter.upper() + ' - ' + item.partner_code
                item.partner_running_number = vendor_code

    @api.multi
    def _get_requestedby_manager(self):
        #search Employee

        user= self.env['res.users']
        user_id = user.search([('id','=',self._get_user().id)])

        #searching Employee Manager

        employeemanager = self.env['hr.employee'].search([('user_id','=',user_id.id)]).parent_id.id
        requested_manager = self.env['hr.employee'].search([('id','=',employeemanager)]).user_id.id
        manager_user = user.search([('id','=',requested_manager)])

        return manager_user

    @api.multi
    def action_confirm(self):
        for item in self:
            check_employee = 0
            arrEmployee = []
            arrParent = []
            hr_employee  = item._get_employee_request()
            employee = item.env['hr.employee']
            for hr in hr_employee:
                arrEmployee.append(hr.id)
            #searching id in parent id employee
            employee_parent_id = employee.search([('parent_id','in',arrEmployee)])

            for parent in employee_parent_id:
                arrParent.append(parent.id)

            if arrParent == []:
                check_employee = check_employee + 1
            item.write(
                {
                 'confirmed_by':item._get_user().id,
                 'assign_to':item._get_requestedby_manager().id if check_employee > 0 else item._get_user().id ,
                 'state':'confirm'}
            )

    @api.multi
    def action_approved(self):
        for item in self:
            if item.assign_to.id != item._get_user().id:
                raise exceptions.ValidationError('User not Match with Field Assign To')
            else:
                item.write(
                    {
                     'partner_code':item.env['ir.sequence'].next_by_code('sequence.vendor'),
                     'approved_by':item._get_user().id,
                     'state':'done'
                    }
                )

    @api.multi
    def action_set_to_draft(self):
        for item in self:
            if item.assign_to.id != item._get_user().id:
                raise exceptions.ValidationError('User not Match with Field Assign To')
            else:
                item.write(
                    {'assign_to':item.confirmed_by.id,
                     'state':'draft'}
                )

    @api.multi
    def action_nonactive(self):
        for item in self:
            item.write({'active':False})

class ResPartnerVendorBusinessPermit(models.Model):

    _name = 'base.indonesia.vendor.business.permit'
    _description = 'Vendor Business Permit and Certificate of Company Registration'

    partner_id = fields.Many2one('res.partner','Res Partner')
    no_identity_business = fields.Char('No SIUP/SIUJK/SIUPAL')
    due_date_business_permit = fields.Date('Due Date Business Permit')
    published_by_business_permit = fields.Char('Published By')
    no_certificate_of_company_registration = fields.Char('No Certificate of Company Registration')
    due_date_certificate_of_company_cegistration = fields.Date('Due Date Certificate of Company Registration')
    published_by_certificate_of_company_cegistration = fields.Char('Published By Certificate of Company Registration')

class ResPartnerTaxes(models.Model):

    _name = 'base.indonesia.taxes'
    _description = 'Partner Taxes'

    partner_id = fields.Many2one('res.partner','Res Partner')
    npwp_no = fields.Char('NPWP No')
    nppkp_no = fields.Char('NPPKP No')




