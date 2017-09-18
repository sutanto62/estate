from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re
import itertools

class InheritPurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    owner_id = fields.Integer('owner id')

class InheritPurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    owner_id = fields.Integer('owner id')

class InheritPurchaseRequest(models.Model):

    @api.multi
    def purchase_request_dpt_head(self):
        return self.env.ref('purchase_request.group_purchase_request_dept_head', False).id

    @api.multi
    def purchase_request_division_head(self):
        return self.env.ref('purchase_request.group_purchase_request_div_head', False).id

    @api.multi
    def purchase_request_budget(self):
        return self.env.ref('purchase_request.group_purchase_request_budget', False).id

    @api.multi
    def purchase_request_technical1(self):
        return self.env.ref('purchase_request.group_purchase_request_technical1', False).id

    @api.multi
    def purchase_request_technical2(self):
        return self.env.ref('purchase_request.group_purchase_request_technical2', False).id

    @api.multi
    def purchase_request_technical3(self):
        return self.env.ref('purchase_request.group_purchase_request_technical3', False).id

    @api.multi
    def purchase_request_technical4(self):
        return self.env.ref('purchase_request.group_purchase_request_technical4', False).id

    @api.multi
    def purchase_request_technical5(self):
        return self.env.ref('purchase_request.group_purchase_request_technical5', False).id

    @api.multi
    def purchase_request_technical6(self):
        return self.env.ref('purchase_indonesia.group_purchase_request_technical6', False).id

    @api.multi
    def purchase_request_director(self):
        return self.env.ref('purchase_indonesia.group_purchase_request_director', False).id

    @api.multi
    def purchase_request_president_director(self):
        return self.env.ref('purchase_indonesia.group_purchase_request_president_director', False).id

    @api.multi
    def purchase_ro_head(self):
        return self.env.ref('purchase_indonesia.group_purchase_request_head_of_ro', False).id

    @api.multi
    def purchase_procurement_staff(self):
        return self.env.ref('purchase_request.group_purchase_request_procstaff', False).id

    @api.multi
    def purchase_request_manager(self):
        return self.env.ref('purchase_request.group_purchase_request_manager', False).id

    @api.multi
    def purchase_request_finance(self):
        return self.env.ref('purchase_request.group_purchase_request_finance_procurement', False).id

    @api.multi
    def purchase_request_estate_manager(self):
        return self.env.ref('estate.group_manager', False).id

    #Method Get user
    @api.multi
    def _get_user(self):
        #find User
        user= self.env['res.users'].browse(self.env.uid)

        return user

    @api.multi
    def _get_employee(self):
        #find User Employee

        employee = self.env['hr.employee'].search([('user_id','=',self._get_user().id)])

        return employee

    @api.multi
    def _get_employee_request(self):
        #find User Employee

        employee = self.env['hr.employee'].search([('user_id','=',self.requested_by.id)])

        return employee

    @api.multi
    def _get_user_manager(self):
        #Find Employee user Manager
        try:
            employeemanager = self.env['hr.employee'].search([('user_id','=',self._get_user().id)]).parent_id.id
            assigned_manager = self.env['hr.employee'].search([('id','=',employeemanager)]).user_id.id
        except:
            raise exceptions.ValidationError('Please Contact your HR Admin to fill your manager')

        if not assigned_manager:
            raise exceptions.ValidationError('Please Contact your HR Admin to fill your manager')

        return assigned_manager

    @api.multi
    def _get_office_level_id(self):

        try:
            employee = self._get_employee().office_level_id.name
        except:
            raise exceptions.ValidationError('Office level Name Is Null')

        return employee

    @api.multi
    def _get_office_level_id_code(self):

        try:
            employee = self._get_employee().office_level_id.code
        except:
            raise exceptions.ValidationError('Office level Code Is Null')

        return employee

    @api.multi
    def _get_department_code(self):
        department_code = []
        for item in self:
            department = item.env['hr.department'].search([])
            for record in department:
                if record.code != 'ICT' and record.code:
                    department_code.append(record.code)
        return department_code

    @api.multi
    def _get_department_not_finance_code(self):
        department_code = []
        for item in self:
            department = item.env['hr.department'].search([])
            for record in department:
                if record.code not in ['PRC','GA','FIN','ACC','BGT']:
                    department_code.append(record.code)
        return department_code

    _inherit = ['purchase.request']
    _rec_name = 'complete_name'
    _order = 'complete_name desc'

    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    type_purchase = fields.Many2one('purchase.indonesia.type','Purchase Type',required=True)
    type_functional = fields.Selection([('agronomy','Agronomy'),
                                     ('technic','Technic'),('general','General')],'Unit Functional')
    department_id = fields.Many2one('hr.department','Department')
    employee_id = fields.Many2one('hr.employee','Employee')
    purchase_ids = fields.One2many('purchase.order','request_id','Purchase Order Line',domain=[('state','!=','cancel')])
    line_product_ids = fields.One2many('purchase.requisition.line','owner_id','Purchase Requisition Line')
    type_location = fields.Char('Location',default=_get_office_level_id,readonly = 1)
    code =  fields.Char('code location',default=_get_office_level_id_code,readonly = 1)
    type_product = fields.Selection([('consu','Capital'),
                                     ('service','Service'),('product','Stockable Product')],'Location Type',required=True)
    type_budget = fields.Selection([('available','Budget Available'),('not','Budget Not Available')])
    tracking_approval_ids = fields.One2many('tracking.approval','owner_id','Tracking Approval List')
    state = fields.Selection(
        selection_add=[('done','Done'),('confirm','Confirm'),
                       ('approval1', 'Dept Head Approval'),
                       ('approval7','RO Head Approval'),
                       ('approval2', 'Div Head Approval'),
                       ('budget', 'Budget Approval'),
                       ('technic1', 'Technic Dept Head Approval'),
                       ('technic2', 'Technic Div Head Approval'),
                       ('technic3', 'Technic ICT Dept Approval'),
                       ('technic4', 'Technic GM Plantation Dept Approval'),
                       ('technic5', 'Technic EA Dept Approval'),
                       ('technic6', 'Technic HR Approval'),
                       ('approval3','Department Head Financial Approval'),
                       ('approval4','Div Head Financial Approval'),
                       ('approval5','Director Financial Approval'),
                       ('approval6','President Director Financial Approval'),
                       ('reject','Reject')])
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    reject_reason = fields.Text('Reject Reason')
    total_estimate_price = fields.Float('Total Estimated Price',compute='_compute_total_estimate_price')
    pta_code =  fields.Char('Additional budget request')
    validation_user = fields.Boolean("Validation User",compute='_change_validation_user')
    validation_reject = fields.Boolean("Validation Reject",compute='_change_validation_reject')
    validation_finance = fields.Boolean("Validation Finance",compute='_change_validation_finance')
    validation_correction = fields.Boolean("Validation Correction",compute='_change_validation_correction')
    validation_technic = fields.Boolean("Validation Technic",compute='_change_validation_technic')
    validation_state_budget = fields.Boolean("Validation Budget",compute='_change_validation_budget')
    validation_correction_procurement = fields.Boolean("Validation Correction Procurement",default=False)
    count_grn_done = fields.Integer('GRN/SRN Done', compute='_compute_grn_or_srn')
    count_grn_assigned = fields.Integer('GRN/SRN Assigned', compute='_compute_grn_or_srn')
    count_po_partial = fields.Integer('PO Partial', compute='_compute_po_line')
    count_po_done = fields.Integer('PO Done', compute='_compute_po_line')
    isByPass =  fields.Boolean("Code By Pass" ,store=False)
    validation_requester = fields.Boolean("Validation Requester",compute='_change_validation_requester')
    count_po = fields.Integer('PO', compute='_compute_po_line')
    count_grn = fields.Integer('GRN/SRN', compute='_compute_grn_or_srn')
    is_confirmation = fields.Boolean('PP Confirmation', default=False)
    active = fields.Boolean('Active', default=True)
    
    @api.multi
    def set_is_confirmation(self,value):
        """ make pp as pp confirmation
        """
        for item in self:
            state_data = {'is_confirmation':value}
            item.write(state_data)
    
    @api.multi
    def _get_type_product(self):
        for item in self:
            if item.type_product == 'consu':
                return True
            elif item.type_product in ['service','product']:
                return False


    @api.multi
    def _get_requestedby_manager(self):
        #search Employee
        user= self.env['res.users'].search([('id','=',self.requested_by.id)])
        #searching Employee Manager
        employeemanager = self.env['hr.employee'].search([('user_id','=',user.id)]).parent_id.id
        requested_manager = self.env['hr.employee'].search([('id','=',employeemanager)]).user_id.id

        return requested_manager


    @api.multi
    def _get_user_ro_manager(self):
        #get List of Ro Manager from user.groups
        arrRO = []

        list_ro_manager = self.env['res.groups'].search([('id','=',self.purchase_ro_head())]).users

        for ro_manager_id in list_ro_manager:
                arrRO.append(ro_manager_id.id)
        try:
            ro_manager = self.env['res.users'].search([('id','in',arrRO)]).id
        except:
            raise exceptions.ValidationError('User Role President Director Not Found in User Access')

        return ro_manager

    @api.multi
    def _get_president_director(self):
        #get List of president director from user.groups
        arrPresidentDirector = []

        #search User President director from user list
        list_president= self.env['res.groups'].search([('id','=',self.purchase_request_president_director())]).users

        for president_id in list_president:
            arrPresidentDirector.append(president_id.id)
        try:
            president = self.env['res.users'].search([('id','=',arrPresidentDirector[0])]).id
        except:
            raise exceptions.ValidationError('User Role President Director Not Found in User Access')
        return president

    @api.multi
    def _get_director(self):
        #get List of director from user.groups
        arrDirector = []

        #search User Director from user list
        list_director= self.env['res.groups'].search([('id','=',self.purchase_request_director())]).users
        for director_id in list_director:
            arrDirector.append(director_id.id)
        try:
            director = self.env['res.users'].search([('id','=',arrDirector[0])]).id
        except:
            raise exceptions.ValidationError('User Role Director Purchase Not Found in User Access')
        return director

    @api.multi
    def _get_division_finance(self):
        #get List of Finance from user.groups
        arrDivhead = []

        #search User Finance from user list
        listdivision= self.env['res.groups'].search([('id','=',self.purchase_request_division_head())]).users

        for divhead in listdivision:
            arrDivhead.append(divhead.id)
        try:
            division = self.env['res.users'].search([('id','=',arrDivhead[0])]).id
        except:
            raise exceptions.ValidationError('User  Role Division Head Not Found in User Access')

        return division

    @api.multi
    def _get_technic_ict(self):
        #get List of Technical Dept ICT from user.groups
        #technical ict in user groups same Like Technic3

        arrTechnic3 = []

        list_technicalict = self.env['res.groups'].search([('id','=',self.purchase_request_technical3())]).users

        for technic3 in list_technicalict:
               arrTechnic3.append(technic3.id)
        try:
            technical_ict = self.env['res.users'].search([('id','=',arrTechnic3[0])]).id
        except:
            raise exceptions.ValidationError('User Technic ICT Not Found in User Access')

        return technical_ict

    @api.multi
    def _get_technic_ga(self):
        #get List of Technical Dept GAfrom user.groups
        #technical GA in user groups same Like Technic6

        arrTechnic6 = []

        list_technicalga = self.env['res.groups'].search([('id','=',self.purchase_request_technical6())]).users

        for technic6 in list_technicalga:
               arrTechnic6.append(technic6.id)
        try:
            technical_ga = self.env['res.users'].search([('id','=',arrTechnic6[0])]).id
        except:
            raise exceptions.ValidationError('User Technic GA Not Found in User Access')

        return technical_ga

    @api.multi
    def _get_technic_agronomy(self):
        #get List of Technical Dept Agronomy from user.groups
        #technical Agronomy in user groups same Like Technic4

        arrTechnic4 = []
        arrEstateManager = []

        estate_manager = self.env['res.groups'].search([('id','=',self.purchase_request_estate_manager())]).users

        technic4 = self.env['res.groups'].search([('id','=',self.purchase_request_technical4())]).users

        for technic4 in technic4:
            arrTechnic4.append(technic4.id)

        for estate in estate_manager:
            arrEstateManager.append(estate.id)

        equals_temp_parent = set(arrTechnic4)-set(arrEstateManager)

        technic_agronomy = list(equals_temp_parent)

        try:
            technical_agronomy = self.env['res.users'].search([('id','in',technic_agronomy)]).id
        except:
            raise exceptions.ValidationError('User Role Technic Agronomy Not Found in User Access')

        return technical_agronomy

    @api.multi
    def _get_budget_manager(self):
        #get List of Budget from user.groups
       arrBudget = []

       list_budget_manager = self.env['res.groups'].search([('id','=',self.purchase_request_budget())]).users

       for budgetgroupsrecord in list_budget_manager:
            arrBudget.append(budgetgroupsrecord.id)
       try:
            budget_manager = self.env['res.users'].search([('id','=',arrBudget[0])]).id
       except:
           raise exceptions.ValidationError('User Role Budget Manager Not Found in User Access')
       return budget_manager

    @api.multi
    def _get_technic_ie(self):
         #get List of Technical Dept IE from user.groups
         #technical IE in user groups same Like Technic5

         arrTechnic5 = []

         list_technic_ie = self.env['res.groups'].search([('id','=',self.purchase_request_technical5())]).users

         for technic5 in list_technic_ie:
               arrTechnic5.append(technic5.id)

         try:
            technical_ie = self.env['res.users'].search([('id','=',arrTechnic5[0])]).id
         except:
             raise exceptions.ValidationError('User Role Technic IE Not Found in User Access')

         return technical_ie

    @api.multi
    def _get_user_agronomy(self):

        arrBudget=[]
        arrDept=[]

        #search User in 2 groups
        budget_manager = self.env['res.groups'].search([('id','=',self.purchase_request_budget())]).users
        dept_manager =  self.env['res.groups'].search([('id','=',self.purchase_request_dpt_head())]).users

        for budgetgroupsrecord in budget_manager:
            arrBudget.append(budgetgroupsrecord.id)
        for deptgroupsrecord in dept_manager:
            arrDept.append(deptgroupsrecord.id)
        try:
            budget_agronomy = self.env['res.users'].search([('id','in',arrBudget),('id','in',arrDept)]).id
        except:
            raise exceptions.ValidationError('User Role  Agronomy Not Found in User Access')

        return budget_agronomy

    @api.multi
    def _check_departement_head(self):

        arrDepartment = []

        assign_department= self.env['res.groups'].search([('id','=',self.purchase_request_dpt_head())]).users


        #Search ID user from user.groups
        for department in assign_department:
            arrDepartment.append(department.id)

        return self._get_user().id in arrDepartment


    @api.multi
    def _get_compare_hr(self):
        #comparing HR Jobs
        for item in self:
            arrJobs = []

            dept_code = item._get_employee().job_id.department_id.id
            jobs_compare_hr = item.env['hr.department'].search([('code','in',['HR','GA'])])

            for record_job in jobs_compare_hr:
                arrJobs.append(record_job.id)

            return dept_code in arrJobs

    @api.multi
    def _get_compare_non_hr(self):
        #Non Comparing Hr Jobs
        arrJobs2 = []

        jobs = self.env['hr.job'].search([('id','=',self._get_employee().job_id.id)]).id
        jobs_non_hr = self.env['hr.job'].search([('name','not in',['HR','hr','HR & GA Head Assistant','hr & GA  Head Assistant',
                                                                   ])])

        for item in jobs_non_hr:
            arrJobs2.append(item.id)

        return jobs in arrJobs2

    @api.multi
    def _get_compare_requester_non_hr(self):
        #Non Comparing Hr Jobs
        arrJobs2 = []

        jobs = self.env['hr.job'].search([('id','=',self._get_employee_request().job_id.id)]).id
        jobs_non_hr = self.env['hr.job'].search([('name','not in',['HR','hr','HR & GA Head Assistant','hr & GA  Head Assistant',
                                                                   'Administration Assistant','KTU','ktu'])])

        for item in jobs_non_hr:
            arrJobs2.append(item.id)

        return jobs in arrJobs2


    #--------------------------end of Method search User--------------------------

    #Method get Pricing
    @api.multi
    def _get_price_low(self):
        #get Minimal price from purchase params for Purchase Request
        try:
            price_standard = self.env['purchase.params.setting'].search([('name','=',self._name)])

            price = min(price.value_params for price in price_standard)
        except:
            raise exceptions.ValidationError('Call Your Procurement Admin To set up the Price')

        return float(price)
    
    @api.multi
    def _get_max_price(self):
        #get total price from purchase request

        price = float(sum(record.total_price for record in self.line_ids))

        return price

    @api.multi
    def _get_total_price_budget(self):
        #get total budget_available from purchase request

        price = float(sum(record.budget_available for record in self.line_ids))

        return price

    @api.multi
    def _get_price_mid(self):
        #get middle price from purchase params for Purchase Request
        arrMid = []
        try:
            price_standard = self.env['purchase.params.setting'].search([('name','=',self._name)])
        except:
            raise exceptions.ValidationError('Call Your Procurement Admin To set up the Price')
        for price in price_standard:
            arrMid.append(price.value_params)
        price = arrMid[1]
        return float(price)

    @api.multi
    def _get_price_high(self):
        #get Maximal price from purchase params for Purchase Request
        try:
            price_standard = self.env['purchase.params.setting'].search([('name','=',self._name)])
            price = max(price.value_params for price in price_standard)
        except:
            raise exceptions.ValidationError('Call Your Procurement Admin To set up the Price')
        return float(price)

    #--------------------------End Of Method Search Price----------------

    #validation
    @api.multi
    def _check_validation_user(self):
        arrDivision = []
        arrTechnic3 = []
        arrTechnic4 = []
        arrTechnic5 = []
        arrBudget = []
        arrRohead = []
        arrDirector = []
        arrPresidentDirector = []

        #search User from res.user
        assign_division= self.env['res.groups'].search([('id','=',self.purchase_request_division_head())]).users
        technic3 = self.env['res.groups'].search([('id','=',self.purchase_request_technical3())]).users
        technic4 = self.env['res.groups'].search([('id','=',self.purchase_request_technical4())]).users
        technic5 = self.env['res.groups'].search([('id','=',self.purchase_request_technical5())]).users
        budget = self.env['res.groups'].search([('id','=',self.purchase_request_budget())]).users
        director= self.env['res.groups'].search([('id','=',self.purchase_request_director())]).users
        president_director = self.env['res.groups'].search([('id','=',self.purchase_request_president_director())]).users
        ro_head = self.env['res.groups'].search([('id','=',self.purchase_ro_head())]).users

        #Search ID user from user.groups

        for division in assign_division:
            arrDivision.append(division.id)
        for budget in budget:
            arrBudget.append(budget.id)
        for technic3 in technic3:
            arrTechnic3.append(technic3.id)
        for technic4 in technic4:
            arrTechnic4.append(technic4.id)
        for technic5 in technic5:
            arrTechnic5.append(technic5.id)
        for director in director:
            arrDirector.append(director.id)
        for president_director in president_director:
            arrPresidentDirector.append(president_director.id)
        for ro_head in ro_head:
            arrRohead.append(ro_head.id)

        validation_reject = False

        if self.assigned_to.id == self._get_user().id and self._check_departement_head and self.state == 'approval1':
            validation_reject = True
        elif self.assigned_to.id == self._get_user().id and self.state in ['draft','confirm']:
            validation_reject = True
        elif self.assigned_to.id == self._get_user().id and self._get_user().id in arrDivision and self.state == 'approval2':
            validation_reject = True
        elif self.assigned_to.id == self._get_user().id and self._get_user().id in arrBudget and self.state == 'budget':
            validation_reject = True
        elif self.assigned_to.id == self._get_user().id and self._get_user().id in arrTechnic3 and self.state == 'technic3':
            validation_reject = True
        elif self.assigned_to.id == self._get_user().id and self._get_user().id in arrTechnic4 and self.state == 'technic4':
            validation_reject = True
        elif self.assigned_to.id == self._get_user().id and self._get_user().id in arrTechnic5 and self.state == 'technic5':
            validation_reject = True
        elif self.assigned_to.id == self._get_user().id and self._check_departement_head and self.state == 'approval3':
            validation_reject = True
        elif self.assigned_to.id == self._get_user().id and self.state == 'approval4':
            validation_reject = True
        elif self.assigned_to.id == self._get_user().id and self._get_user().id in arrDirector and self.state == 'approval5':
            validation_reject = True
        elif self.assigned_to.id == self._get_user().id and self._get_user().id in arrPresidentDirector and self.state == 'approval6':
            validation_reject = True
        elif self.assigned_to.id == self._get_user().id and self._get_user().id in arrRohead and self.state == 'approval7':
            validation_reject = True

        return validation_reject

    #Button Workflow
    @api.multi
    def button_rejected(self):
        self.write({'state': 'reject', 'date_request': self.date_start})
        self.write({'description':self.reject_reason})
        return True

    @api.multi
    def action_revert(self):
        """ revert approval to financial approval.
        """
        state_data = {'state':'approval4','assigned_to' : self._get_division_finance()}
        self.write(state_data)
        self.send_mail_template()

    @api.multi
    def action_financial_approval1(self):
        """ Confirms department Head Financial Approval.
        """
        if self._get_total_price_budget() < self._get_price_low():
            self.button_approved()
        elif self._get_total_price_budget() >= self._get_price_low():
            state_data = {'state':'approval4','assigned_to':self._get_division_finance()}
            self.write(state_data)
            self.send_mail_template()

    @api.multi
    def action_financial_approval2(self):
        """ Confirms Division Head Financial Approval.
        """
#         for item in self:
#             if item.code in ['KPST'] and item._get_total_price_budget() < item._get_price_mid():
#                 item.button_approved()
#             elif item.code in ['KOKB'] and item.department_id.code not in item._get_department_not_finance_code() and item._get_total_price_budget() < item._get_price_mid():
#                 item.button_approved()
#             elif (item.code in ['KOKB']
#                 and item.department_id.code in item._get_department_not_finance_code()
#                 and (item._get_total_price_budget() >= item._get_price_mid()
#                 or item._get_total_price_budget() < item._get_price_mid())) \
#                 or (item.code in ['KPST'] and item._get_total_price_budget() >= item._get_price_mid()):
#                 state_data = {'state':'approval5','assigned_to' : item._get_director()}
#                 item.write(state_data)
#                 item.send_mail_template()
        
        for item in self:
            if item.code in ['KPST'] and item._get_total_price_budget() < item._get_price_mid():
                item.button_approved()
            elif item.code in ['KOKB'] and item.department_id.code not in item._get_department_not_finance_code() and item._get_total_price_budget() < item._get_price_mid():
                item.button_approved()
            else :
                state_data = {'state':'approval5','assigned_to' : item._get_director()}
                item.write(state_data)
                item.send_mail_template()

        # elif self._get_type_product() == False:
            #Product service and stockable
            # if self._get_max_price() < self._get_price_mid():
            #         self.button_approved()
            # elif self._get_max_price() >= self._get_price_mid():
            #     state_data = {'state':'approval5','assigned_to' : self._get_director()}
            #     self.write(state_data)
            #     self.send_mail_template()

    @api.multi
    def action_financial_approval3(self):
        """ Confirms Director  Financial Approval.
        """
        # if self._get_type_product() == True:
        if self._get_total_price_budget() < self._get_price_high():
                self.button_approved()
        elif self._get_total_price_budget() >= self._get_price_high():
            state_data = {'state':'approval6','assigned_to' : self._get_president_director()}
            self.write(state_data)
            self.send_mail_template()
        # elif self._get_type_product() == False:
        #     if self._get_max_price() < self._get_price_high():
        #             self.button_approved()
        #     elif self._get_max_price() >= self._get_price_high():
        #         state_data = {'state':'approval6','assigned_to' : self._get_president_director()}
        #         self.write(state_data)
        #         self.send_mail_template()

    @api.multi
    def action_financial_approval4(self):
        """ Confirms President Director Approval.
        """
        self.button_approved()

    @api.multi
    def button_approved(self):
        for item in self:
            arrRequisition = []
            requisition = item.env['purchase.requisition']

            requisition_id = requisition.search([('request_id','=',item.id)])
            for id in requisition_id:
                arrRequisition.append(id.request_id.id)

            if item.validation_correction_procurement == True:
                if item.id in arrRequisition:

                    item.update_purchase_requisition()
                else:

                    item.tracking_approval()
                    item.create_purchase_requisition()
                    item.create_quotation_comparison_form()
            else:
                item.tracking_approval()
                item.create_purchase_requisition()
                item.create_quotation_comparison_form()
            super(InheritPurchaseRequest, item).button_approved()
            return True

    @api.multi
    def action_confirm1(self,):
        """ Confirms User request.
        """
        self.check_wkf_product_price()
        return True

    @api.multi
    def action_confirm2(self,):
        """ Confirms Good request.
        """
        self.write({'state': 'budget','assigned_to':self._get_budget_manager()})
        self.send_mail_template()
        
    @api.multi
    def action_budget(self,):
        """ Confirms Budget request.
        """
        state_data = []
        if self.type_budget== 'not' and not self.pta_code:
            raise exceptions.ValidationError('Input Your PTA Number')
        elif self.type_functional == 'general' and self.department_id.code in self._get_department_code()and self._get_total_price_budget() < self._get_price_low():
            if self.product_category_id.get_technical_checker():
                state_data = {'state':'technic3','assigned_to':self.product_category_id.get_technical_checker().id}
                self.write(state_data)
                self.send_mail_template()
            else:
                self.button_approved()
        else:
            try:
               if self.type_functional == 'agronomy' and self._get_total_price_budget() < self._get_price_low() or self.type_functional == 'agronomy' and self._get_total_price_budget() >= self._get_price_low():
                    state_data = {'state':'technic4','assigned_to':self._get_technic_agronomy()}
               elif self.type_functional == 'technic' and self._get_total_price_budget() < self._get_price_low() or self.type_functional == 'technic' and self._get_total_price_budget() >= self._get_price_low():
                    state_data = {'state':'technic5','assigned_to':self._get_technic_ie()}
               elif (self.type_functional == 'general' and self.department_id.code not in self._get_department_code()and self._get_total_price_budget() < self._get_price_low()) or (self.type_functional == 'general' and self.department_id.code not in self._get_department_code() and self._get_total_price_budget() >= self._get_price_low()) :
                    state_data = {'state':'technic3','assigned_to':self.product_category_id.get_technical_checker().id}
               elif self.type_functional == 'general' and self.department_id.code in self._get_department_code()and self._get_total_price_budget() < self._get_price_low():
                    if self.product_category_id.get_technical_checker():
                        state_data = {'state':'technic3','assigned_to':self.product_category_id.get_technical_checker().id}
                    else:
                        state_data = {'state':'technic6','assigned_to':self._get_technic_ga()}
               elif self.type_functional == 'general' and self.department_id.code in self._get_department_code() and self._get_total_price_budget() >= self._get_price_low() :
                    if self.product_category_id.get_technical_checker():
                        state_data = {'state':'technic3','assigned_to':self.product_category_id.get_technical_checker().id}
                    else:
                        state_data = {'state':'approval4','assigned_to':self._get_division_finance()}
            except: 
                raise exceptions.ValidationError('Call Your Hr Admin to Fill Department Code')
            self.write(state_data)
            self.send_mail_template()

    @api.multi
    def action_technic(self):
        """ Confirms Technical request.
        """
        if self.type_functional == 'agronomy' and self._get_total_price_budget() < self._get_price_low():
            self.button_approved()
        elif self.type_functional == 'general' and self._get_total_price_budget() < self._get_price_low():
            self.button_approved()
        elif self.type_functional == 'technic' and self._get_total_price_budget() < self._get_price_low():
            self.button_approved()
        elif self._get_total_price_budget() >= self._get_price_low() or self._get_compare_requester_non_hr():
            state_data = {'state':'approval4','assigned_to':self._get_division_finance()}
            self.write(state_data)
            self.send_mail_template()
        else:
            raise exceptions.ValidationError('Call Your Hr Admin to fill Your Jobs')

    @api.model
    def create(self, vals):
        try:
            company_code = self.env['res.company'].search([('id','=',vals['company_id'])]).code
        except:
            raise exceptions.ValidationError('Company Code is Null')


        location_code = self._get_employee().office_level_id.code

        try:
            sequence_name = 'purchase.request.seq.'+location_code.lower()+'.'+company_code.lower()
            vals['name']=self.env['ir.sequence'].next_by_code(sequence_name)
        except:
            error_msg = "Employee Office Level Code is Null for %s" %(self._get_employee().name)
            raise exceptions.ValidationError(error_msg)

        request = super(InheritPurchaseRequest, self).create(vals)
        return request



    @api.multi
    def check_wkf_requester(self):
        #checking Approval Requester
        for item in self:
            state_data = []
            if item._get_compare_hr() and item.code in ['KOKB']:
                item.write({'state':'confirm'})
                state_data = {'state':'approval7','assigned_to':item._get_user_ro_manager()}
            elif item._get_compare_hr() and item.code in ['KPST']:
                item.write({'state':'confirm'})
                state_data = {'state':'approval1','assigned_to':item._get_user_manager()}
            elif (item._get_compare_non_hr() and item.code in ['KOKB']) or (item._get_compare_non_hr()and item.code in ['KPST']):
                item.write({'state':'confirm'})
                state_data = {'state':'approval1','assigned_to':item._get_user_manager()}

            else:
                raise exceptions.ValidationError('Call Your Hr Admin to fill Your Jobs')

            item.write(state_data)
            item.send_mail_template()

    @api.multi
    def action_ro_head_approval(self):
        #Action Approval RO Head
        state_data = []

        if self._get_max_price() >= self._get_price_low():
            state_data = {'state':'budget','assigned_to':self._get_budget_manager()}

        elif self.type_functional == 'agronomy' and self._get_max_price() < self._get_price_low() :
            state_data = {'state':'budget','assigned_to':self._get_budget_manager()}

        elif self.type_functional == 'technic' and self._get_max_price() < self._get_price_low():
            state_data = {'state':'budget','assigned_to':self._get_budget_manager()}

        elif self.type_functional == 'general' and self._get_max_price() < self._get_price_low():
            state_data = {'state':'budget','assigned_to':self._get_budget_manager()}
        else:
            raise exceptions.ValidationError('Call Your Procurement Admin To Set Rule of Price')

        self.write(state_data)
        self.send_mail_template()

    @api.multi
    def check_wkf_product_price(self):
       #check total product price in purchase request
       state_data = []
       if self.code in ['KOKB']:
          self.write({'state':'confirm'})
          state_data = {'state':'approval7','assigned_to':self._get_user_ro_manager()}
       else:
           if self._get_max_price() >= self._get_price_low() and self._get_employee_request().parent_id.id:
               if self._get_employee().parent_id.user_id.id == self._get_division_finance():
                   state_data = {'state':'budget','assigned_to':self._get_budget_manager()}
               else:
                   state_data = {'state':'approval2','assigned_to':self._get_employee_request().parent_id.user_id.id}
           elif (self._get_max_price() >= self._get_price_low() and not self._get_employee().parent_id.id) or (self.type_functional == 'agronomy' and self._get_max_price() < self._get_price_low()) or (self.type_functional == 'technic' and self._get_max_price() < self._get_price_low()) or (self.type_functional == 'general' and self._get_max_price() < self._get_price_low()) :
                state_data = {'state':'budget','assigned_to':self._get_budget_manager()}
           else:
              raise exceptions.ValidationError('Call Your Procurement Admin To Set Rule of Price')

       self.write(state_data)
       self.send_mail_template()

    @api.multi
    def tracking_approval(self):
        user= self.env['res.users'].browse(self.env.uid)
        employee = self.env['hr.employee'].search([('user_id','=',user.id)]).name_related
        current_date=str(datetime.now().today())
        tracking_data = {
            'owner_id': self.id,
            'state' : self.state,
            'name_user' : employee,
            'datetime'  :current_date
        }
        self.env['tracking.approval'].create(tracking_data)


    @api.multi
    def create_purchase_requisition(self):
        # Create Purchase Requisition
        for purchase in self:
            purchase_data = {
                'companys_id' :purchase.company_id.id,
                'location':purchase.type_location,
                'type_location' : purchase.code,
                'origin': purchase.complete_name,
                'request_id':purchase.id,
                'ordering_date' : datetime.today(),
                'owner_id' : purchase.id
            }
            res = self.env['purchase.requisition'].create(purchase_data)
            res.send_mail_template_new_tender()

        for purchaseline in self.env['purchase.request.line'].search([('request_id.id','=',self.id)]):
            purchaseline_data = {
                'product_id': purchaseline.product_id.id,
                'est_price':purchaseline.price_per_product,
                'product_uom_id': purchaseline.product_uom_id.id,
                'product_qty' : purchaseline.product_qty if purchaseline.control_unit == 0 else purchaseline.control_unit,
                'requisition_id' : res.id,
                'owner_id' :res.owner_id
            }
            self.env['purchase.requisition.line'].create(purchaseline_data)

        return True

    @api.multi
    def update_purchase_requisition(self):
        # Update Purchase Requisition
        requisition=self.env['purchase.requisition'].search([('request_id','=',self.id)])
        update_requisition = requisition.write({'state':'in_progress'})
        requisition_id = requisition.id
        for purchaseline in self.env['purchase.request.line'].search([('request_id.id','=',self.id)]):
            purchaseline_data = {

                'product_id': purchaseline.product_id.id,
                'est_price':purchaseline.price_per_product,
                'product_uom_id': purchaseline.product_uom_id.id,
                'product_qty' : purchaseline.product_qty if purchaseline.control_unit == 0 else purchaseline.control_unit,
            }
            self.env['purchase.requisition.line'].search([('requisition_id','=',requisition_id),('product_id','=',purchaseline.product_id.id)]).write(purchaseline_data)

        return True

    @api.multi
    def create_quotation_comparison_form(self):
        purchase_requisition = self.env['purchase.requisition'].search([('origin','like',self.complete_name)])
        try:
            company_code = self.env['res.company'].search([('id','=',self.company_id.id)]).code
        except:
            raise exceptions.ValidationError('Company Code is Null')
        sequence_name = 'quotation.comparison.form.'+self.code.lower()+'.'+company_code.lower()
        purchase_data = {
                'name' : self.env['ir.sequence'].next_by_code(sequence_name),
                'company_id': purchase_requisition.companys_id.id,
                'date_pp': datetime.today(),
                'requisition_id': purchase_requisition.id,
                'origin' : purchase_requisition.origin,
                'type_location' : purchase_requisition.type_location,
                'location':purchase_requisition.location,
                'state':'draft'
            }
        res = self.env['quotation.comparison.form'].create(purchase_data)
    
    def _change_validation_requester(self):
        self.validation_requester = False
        if self.requested_by.id == self._get_user().id and self.state == 'draft' :
            self.validation_requester = True
        
    @api.multi
    @api.depends('assigned_to')
    def _change_validation_user(self):
        if self.assigned_to.id == self._get_user().id and self._check_departement_head and self.state == 'approval1':
            self.validation_user = True

    @api.depends('assigned_to')
    def _change_validation_finance(self):

        if self.assigned_to.id == self._get_user().id and self.state == 'approval3':
            self.validation_finance = True

    @api.depends('assigned_to')
    def _change_validation_correction(self):

        if self.assigned_to.id == self._get_user().id and self.state in ['approval5','approval6']:
            self.validation_correction = True

    @api.depends('assigned_to')
    def _change_validation_technic(self):

        if self.assigned_to.id == self._get_user().id and self.state in ['technic1','technic2','technic3','technic4','technic5','technic6']:
            self.validation_technic = True

    @api.multi
    @api.depends('assigned_to')
    def _change_validation_budget(self):

        if self.assigned_to.id == self._get_user().id and self.state in ['budget','approval4','approval5','approval6']:
            self.validation_state_budget = True

    @api.multi
    @api.depends('assigned_to')
    def _change_validation_reject(self):
        self.validation_reject = self._check_validation_user()

    @api.one
    @api.depends('name','date_start','company_id','department_id')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d'

        if self.name and self.date_start and self.company_id.code and self.department_id:
            date = self.date_start
            conv_date = datetime.strptime(str(date), fmt)
            month = conv_date.month
            year = conv_date.year

            #change integer to roman
            if type(month) != type(1):
                raise TypeError, "expected integer, got %s" % type(month)
            if not 0 < month < 4000:
                raise ValueError, "Argument must be between 1 and 3999"
            ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
            nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
            result = ""
            for i in range(len(ints)):
              count = int(month / ints[i])
              result += nums[i] * count
              month -= ints[i] * count
            month = result

            departement_code = ''
            employee_code = ''

            #get Employee Code
            try:
                employee_code = self._get_employee().office_level_id.code
            except:
                error_msg = "Employee Office Level Code is Null for %s" %(self._get_employee().name)
                raise exceptions.ValidationError(error_msg)
           
            type_location = employee_code

            try :
                departement_code = self.department_id.code
            except:
                departement_code = self.department_id.name

            if self.department_id.code == False:
                error_msg = "Employee Department Code is Null for %s" %(self._get_employee().name)
                raise exceptions.ValidationError(error_msg)
            else:
                self.complete_name = self.name + '/' \
                                         + self.company_id.code+'-'\
                                         +'PP'+'/'\
                                         +type_location+'/'+departement_code+'/'+str(month)+'/'+str(year)
        else:
            self.complete_name = self.name

        return True

    @api.multi
    def print_purchase_request(self):
        return self.env['report'].get_action(self, 'purchase_indonesia.report_purchase_request')

    @api.multi
    @api.depends('line_ids')
    def _compute_total_estimate_price(self):
        for item in self:
            item.total_estimate_price = sum(record.total_price for record in item.line_ids)

    @api.multi
    @api.onchange('type_location')
    def _onchange_functional(self):
        if self._get_office_level_id_code() == 'KPST':
            self.type_functional = 'general'
        else:
            self.type_functional

    # @api.multi
    # @api.onchange('company_id')
    # def _onchange_company_id(self):
    #
    #     if self._get_employee().company_id.id:
    #         self.company_id = self._get_employee().company_id.id

    @api.multi
    @api.onchange('requested_by')
    def _onchange_assigned_to(self):
        if self.requested_by and not self.assigned_to.id:
            assigned_manager = self.env['res.users'].search([('id','=',self.requested_by.id)]).id
            self.assigned_to = assigned_manager

    @api.multi
    @api.onchange('type_functional')
    def _onchange_department(self):
        arrDepartment = []
        arr_agronomy = ['AGR','PRL']
        arr_technic = ['IE']
        arr_agronomy_technic = ['AGR','PRL','IE']
        if self.type_functional == 'agronomy':
            department = self.env['hr.department'].search([('code','in',arr_agronomy)])
            for department in department:
                arrDepartment.append(department.id)
            return {
                'domain':{
                    'department_id':[('id','in',arrDepartment)]
                }
            }
        if self.type_functional == 'technic':
            department = self.env['hr.department'].search([('code','in',arr_technic)])
            for department in department:
                arrDepartment.append(department.id)
            return {
                'domain':{
                    'department_id':[('id','in',arrDepartment)]
                }
            }
        if self.type_functional == 'general':
            department = self.env['hr.department'].search([('code','not in',arr_agronomy_technic),('code','!=','False')])
            for department in department:
                arrDepartment.append(department.id)
            return {
                'domain':{
                    'department_id':[('id','in',arrDepartment)]
                }
            }

    @api.multi
    @api.onchange('department_id')
    def _onchange_employee(self):
        #onchange employee by Department
        arrEmployee=[]
        if self.department_id:

            employee = self.env['hr.employee'].search([('department_id.id','=',self.department_id.id)])
            for employeelist in employee:
                arrEmployee.append(employeelist.id)
            return {
                'domain':{
                    'employee_id' :[('id','in',arrEmployee)]
                }
            }

    @api.multi
    @api.onchange('employee_id')
    def _onchange_department_from_employee(self):

        if self.employee_id:
           self.assigned_to = self.employee_id.parent_id.id
           self.department_id = self.employee_id.department_id.id
           self.company_id = self.employee_id.company_id.id
           department1 = self.env['hr.department'].search([('name','in',['agronomi','Agronomi','Agronomy','agronomy','PR & LA','Pr & La','PR&LA','pr & la','pr&la'])])
           department2 = self.env['hr.department'].search([('name','in',['IE','transport & workshop','Transport & Workshop'])])
           department3 = self.env['hr.department'].search([('name','in',['HR & GA','HR','GA','ICT','Finance','Legal','Procurement','GIS','RO'])])
           if department1 :
                self.type_functional = 'agronomy'
           if department2 :
                self.type_functional = 'technic'
           if department3 :
                self.type_functional = 'general'

    @api.multi
    @api.onchange('line_ids')
    def _onchange_budget_type(self):
        arrBudget = []
        for item in self.line_ids:
            if item.budget_available <= 0:
                self.type_budget = 'not'
            if item.budget_available > 0:
                self.type_budget = 'available'

    @api.multi
    @api.constrains('line_ids')
    def _constraint_line_ids(self):
        #constraint to line ids
        for item in self.line_ids:

            if item.price_per_product <=0:
                raise exceptions.ValidationError('Call Your Procurment Admin to Fill last Cost')

    @api.multi
    @api.constrains('line_ids','type_functional','department_id')
    def _constraint_line_ids_category_id(self):
        if self.department_id and self.type_functional :
            mapping_functional = self.env['mapping.department.product'].search([('type_functional','=',self.type_functional),
                                                                        ('department_id.id','=',self.department_id.id)])
            temp_category = []
            temp_line = []
            temp_product_template = []
            temp_name = []
            temp_line_parent = []
            for record in mapping_functional:
                #Search Product Category in mapping functional
                temp_category.append(record.product_category_id.id)

            for item in self.line_ids:
                #Search Product Category in Purchase Request Line
                temp_product_template.append(item.product_id.product_tmpl_id.id)
                temp_line.append(item.product_id.categ_id.id)
                temp_line_parent.append(item.product_id.categ_id.parent_id.id)

            #second Way to Use Combining Sets temp_category and Sets temp line
            equals_temp = set(temp_line) - set(temp_category)
            list_equals = list(equals_temp)

            equals_temp_parent = set(temp_line_parent)-set(temp_category)
            list_equals_parent = list(equals_temp_parent)

            #Search Product Name
            product_template = self.env['product.template'].search([('id','in',temp_product_template),('categ_id','in',list_equals)])
            for name in product_template:
                temp_name.append(name.name)

            if list_equals != [] and list_equals_parent != []:
                 error_msg = "Product \"%s\" is not in Department \"%s\" Product Category" % (temp_name[0],self.department_id.name)
                 raise exceptions.ValidationError(error_msg)

    @api.multi
    @api.depends('purchase_ids')
    def _compute_grn_or_srn(self):
        for item in self:
            arrPickingDone = []
            arrPickingAssigned = []
            done = item.env['stock.picking'].search([('pr_source','in',[item.complete_name]),('state','=','done')])
            assigned = item.env['stock.picking'].search([('pr_source','in',[item.complete_name]),('state','=','assigned')])
            for itemDone in done:
                arrPickingDone.append(itemDone.id)
            for itemAssign in assigned:
                arrPickingAssigned.append(itemAssign.id)
            assign_picking_done = item.env['stock.picking'].search([('id','in',arrPickingDone)])
            assign_picking_assigned = item.env['stock.picking'].search([('id','in',arrPickingAssigned)])
            picking_done = len(assign_picking_done)
            picking_assigned = len(assign_picking_assigned)

            item.count_grn_done = picking_done
            item.count_grn_assigned = picking_assigned
            item.count_grn = picking_assigned + picking_done

    @api.multi
    @api.depends('purchase_ids')
    def _compute_po_line(self):
        for item in self:
            purchase = item.env['purchase.order']
            purchase_done = purchase.search([('request_id','=',item.id),('state','=','done')])
            purchase_partial = purchase.search([('request_id','=',item.id),('state','=','received_force_done')])
            purchase_all = purchase.search([('request_id','=',item.id),('state','=','purchase')])
            
            done = len(purchase_done)
            partial = len(purchase_partial)
            po_purchase = len(purchase_all)
            
            item.count_po_partial = partial
            item.count_po_done = done
            item.count_po = po_purchase + done + partial

    @api.multi
    @api.constrains('line_ids')
    def _constrains_product_purchase_request_id(self):
        self.ensure_one()
        if self.line_ids:
            temp={}
            for part in self.line_ids:
                part_value_name = part.product_id.name
                if part_value_name in temp.values():
                    error_msg = "Product \"%s\" is set more than once " % part_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[part.id] = part_value_name
            return temp

    @api.multi
    @api.constrains('line_ids')
    def _constraint_product_line_not_null(self):
        len_line_ids = len(self.line_ids)
        for item in self:
            if len_line_ids == 0:
                error_msg = "Please Fill Your Product"
                raise exceptions.ValidationError(error_msg)

    #Email Template Code Starts Here

    @api.one
    def send_mail_template(self):
            # Find the e-mail template
            template = self.env.ref('purchase_indonesia.email_template_purchase_request')
            # You can also find the e-mail template like this:
            # template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
            # Send out the e-mail template to the user
            self.env['mail.template'].browse(template.id).send_mail(self.id,force_send=True)

    @api.multi
    def database(self):
        for item in self:
            db = item.env.cr.dbname

            return db

    @api.multi
    def web_url(self):
        for item in self:
            web = item.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return web

    @api.multi
    def email_model(self):
        for item in self:
            model = item._name
            return model

class InheritPurchaseRequestLine(models.Model):

    _inherit = 'purchase.request.line'
    _description = 'Inherit Purchase Request Line'

    @api.multi
    @api.depends('product_id', 'name', 'product_uom_id', 'product_qty',
                 'analytic_account_id', 'date_required', 'specifications','price_per_product_label')
    def _compute_is_editable(self):
#         for rec in self:
#             if rec.request_id.state in ['draft','approval4','approval5','approval6']:
#                 rec.is_editable = True
#             else:
#                 rec.is_editable = False
        for rec in self:
            rec.is_editable = False
            if rec.request_id.state:
                if rec.request_id.state not in ['technic1','technic2','technic3','technic4','technic5','technic6','done','approved','rejected']:
                    rec.is_editable = True

    price_per_product = fields.Float('Product Price')
    price_per_product_label = fields.Char('Product Price',readonly=True)
    total_price = fields.Float('Total Price',compute='_compute_total_price')
    budget_available = fields.Float('Budget Price')
    control_unit =  fields.Float('Budget Control Unit')
    validation_budget = fields.Boolean('Validation Budget',store=False,compute='_compute_validation_budget')

    @api.multi
    @api.onchange('request_id')
    def _compute_validation_budget(self):
        for item in self:
            if item.request_id.validation_state_budget:
                item.validation_budget = item.request_id.validation_state_budget


    @api.multi
    @api.depends('price_per_product','product_qty')
    def _compute_total_price(self):
        for price in self:
            if price.product_qty and price.price_per_product:
                price.total_price = price.product_qty * price.price_per_product

    @api.multi
    @api.onchange('price_per_product','control_unit')
    def _compute_total_budget_price(self):
        for price in self:
            if price.price_per_product and price.control_unit:
                price.budget_available = price.control_unit * price.price_per_product


    @api.multi
    @api.onchange('product_qty')
    def _onchange_control_unit(self):
        for price in self:
            if price.product_qty:
                price.control_unit = price.product_qty


    @api.multi
    @api.onchange('product_id','request_state')
    def _compute_price_per_product(self):
        user= self.env['res.users'].browse(self.env.uid)
        if self.product_id:
            if user.id == self.request_id.assigned_to.id and self.request_id.state not in ['done','approved','rejected']:
                product_temp = self.env.cr.execute('select cost from product_price_history where product_id = %d order by id desc limit 1' %(self.product_id.id))
                line = self.env.cr.fetchone()[0]
                self.price_per_product = line
                self.price_per_product_label = str(line)
            else:
                error_msg = "Only approver can change the detail of product and status is not in either Done, PP Full Approve or Rejected"
                raise exceptions.ValidationError(error_msg)

    @api.multi
    @api.constrains('budget_available')
    def _constraint_budget_available(self):
        for item in self:
             if item.request_state == 'budget' and item.budget_available == 0:
                error_msg = "Please Insert Budget Price"
                raise exceptions.ValidationError(error_msg)


    # @api.multi
    # @api.onchange('analytic_account_id')
    # def _onchange_budget_available(self):
    #     arrBudget = []
    #     if self.analytic_account_id:
    #         budget = self.env['crossovered.budget.lines'].search([('analytic_account_id','=',self.analytic_account_id.id)])
    #         for budget in budget:
    #             arrBudget.append(budget.planned_amount)
    #         for amount in arrBudget:
    #             amount = float(amount)
    #             self.budget_available = amount

    @api.multi
    @api.onchange('request_id','product_id')
    def _onchange_product_purchase_request_line(self):
        #use to onchange domain product same as product_category
        for item in self:
            if item.request_id.type_functional and item.request_id.department_id and item.request_id.type_product:
                arrProductCateg = []
                mappingFuntional = item.env['mapping.department.product'].search([('type_functional','=',item.request_id.type_functional),
                                                                                      ('department_id.id','=',item.request_id.department_id.id)])

                for productcateg in mappingFuntional:
                    arrProductCateg.append(productcateg.product_category_id.id)

                arrProdCatId = []
                prod_categ = item.env['product.category'].search([('parent_id','in',arrProductCateg)])

                for productcategparent in prod_categ:
                    arrProdCatId.append(productcategparent.id)



                if prod_categ :
                    if item.request_id.type_product == 'service':
                        return  {
                            'domain':{
                                'product_id':[('categ_id','in',arrProdCatId),('type','=','service')]
                                 }
                            }
                    elif item.request_id.type_product == 'consu':
                        return  {
                            'domain':{
                                'product_id':['&',('categ_id','in',arrProdCatId),'|',('type_machine','=',True),
                                                                              '|',('type_tools','=',True),
                                                                              '|',('type_other','=',True),
                                                                              ('type_computing','=',True)]
                                 }
                            }
                    elif item.request_id.type_product == 'product':
                        return  {
                            'domain':{
                                'product_id':['&',('categ_id','in',arrProdCatId),('type','=','product'),
                                                                            '&',('type_machine','=',False),
                                                                              '&',('type_tools','=',False),
                                                                              '&',('type_other','=',False),
                                                                              ('type_computing','=',False)]
                                 }
                            }
                elif prod_categ != ():
                    if item.request_id.type_product == 'service':
                        return  {
                        'domain':{
                            'product_id':[('categ_id','in',arrProductCateg),('type','=','service')]
                             }
                        }
                    elif item.request_id.type_product == 'consu':
                        return  {
                        'domain':{
                            'product_id':['&',('categ_id','in',arrProductCateg),'|',('type_machine','=',True),
                                                                              '|',('type_tools','=',True),
                                                                              '|',('type_other','=',True),
                                                                              ('type_computing','=',True)]
                             }
                        }
                    elif item.request_id.type_product == 'product':
                        return  {
                        'domain':{
                            'product_id':['&',('categ_id','in',arrProductCateg),('type','=','product'),
                                                                            '&',('type_machine','=',False),
                                                                              '&',('type_tools','=',False),
                                                                              '&',('type_other','=',False),
                                                                              ('type_computing','=',False)]
                             }
                        }








