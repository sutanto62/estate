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

class InheritPurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    owner_id = fields.Integer('owner id')

class InheritPurchaseRequest(models.Model):

    @api.multi
    def purchase_request_dpt_head(self):
        return 'Purchase Request Department Head'

    @api.multi
    def purchase_request_division_head(self):
        return 'Purchase Request Division Head'

    @api.multi
    def purchase_request_budget(self):
        return 'Purchase Request Budget'

    @api.multi
    def purchase_request_technical1(self):
        return 'Purchase Request Technical Dept Head'

    @api.multi
    def purchase_request_technical2(self):
        return 'Purchase Request Technical Div Head'

    @api.multi
    def purchase_request_technical3(self):
        return 'Purchase Request Technical ICT'

    @api.multi
    def purchase_request_technical4(self):
        return 'Purchase Request Technical Agronomy'

    @api.multi
    def purchase_request_technical5(self):
        return 'Purchase Request Technical IE'

    @api.multi
    def purchase_request_director(self):
        return 'Purchase Request Director'

    @api.multi
    def purchase_request_president_director(self):
        return 'Purchase Request President Director'

    @api.multi
    def purchase_ro_head(self):
        return 'Purchase Request RO Head'

    @api.multi
    def purchase_procurement_staff(self):
        return 'Purchase Request Procurment Staff'

    @api.multi
    def purchase_request_manager(self):
        return 'Purchase Request Manager'

    @api.multi
    def purchase_request_finance(self):
        return 'Purchase Request Finance Procurement'

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

    _inherit = ['purchase.request']
    _rec_name = 'complete_name'
    _order = 'complete_name desc'

    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    type_purchase = fields.Many2one('purchase.indonesia.type','Purchase Type')
    type_functional = fields.Selection([('agronomy','Agronomy'),
                                     ('technic','Technic'),('general','General')],'Unit Functional')
    department_id = fields.Many2one('hr.department','Department')
    employee_id = fields.Many2one('hr.employee','Employee')
    type_location = fields.Char('Location',default=_get_office_level_id,readonly = 1)
    code =  fields.Char('code location',default=_get_office_level_id_code,readonly = 1)
    type_product = fields.Selection([('consu','Capital'),
                                     ('service','Service'),('product','Stockable Product')],'Location Type')
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
    validation_state_budget = fields.Boolean("Validation Budget",compute='_change_validation_budget')
    isByPass =  fields.Boolean("Code By Pass" ,store=False)


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

        list_ro_manager = self.env['res.groups'].search([('name','like',self.purchase_ro_head())]).users

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
        list_president= self.env['res.groups'].search([('name','like',self.purchase_request_president_director())]).users

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
        list_director= self.env['res.groups'].search([('name','like',self.purchase_request_director())]).users
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
        listdivision= self.env['res.groups'].search([('name','like',self.purchase_request_division_head())]).users

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

        list_technicalict = self.env['res.groups'].search([('name','like',self.purchase_request_technical3())]).users

        for technic3 in list_technicalict:
               arrTechnic3.append(technic3.id)
        try:
            technical_ict = self.env['res.users'].search([('id','=',arrTechnic3[0])]).id
        except:
            raise exceptions.ValidationError('User Technic ICT Not Found in User Access')

        return technical_ict

    @api.multi
    def _get_technic_agronomy(self):
        #get List of Technical Dept Agronomy from user.groups
        #technical Agronomy in user groups same Like Technic4

        arrTechnic4 = []

        technic4 = self.env['res.groups'].search([('name','like',self.purchase_request_technical4())]).users

        for technic4 in technic4:
               arrTechnic4.append(technic4.id)

        try:
            technical_agronomy = self.env['res.users'].search([('id','=',arrTechnic4[0])]).id
        except:
            raise exceptions.ValidationError('User Role Technic Agronomy Not Found in User Access')

        return technical_agronomy

    @api.multi
    def _get_budget_manager(self):
        #get List of Budget from user.groups
       arrBudget = []

       list_budget_manager = self.env['res.groups'].search([('name','like',self.purchase_request_budget())]).users

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

         list_technic_ie = self.env['res.groups'].search([('name','like',self.purchase_request_technical5())]).users

         for technic5 in list_technic_ie:
               arrTechnic5.append(technic5.id)

         try:
            technical_agronomy = self.env['res.users'].search([('id','=',arrTechnic5[0])]).id
         except:
             raise exceptions.ValidationError('User Role Technic IE Not Found in User Access')

         return technical_agronomy

    @api.multi
    def _get_user_agronomy(self):

        arrBudget=[]
        arrDept=[]

        #search User in 2 groups
        budget_manager = self.env['res.groups'].search([('name','like',self.purchase_request_budget())]).users
        dept_manager =  self.env['res.groups'].search([('name','like',self.purchase_request_dpt_head())]).users

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

        assign_department= self.env['res.groups'].search([('name','like',self.purchase_request_dpt_head())]).users


        #Search ID user from user.groups
        for department in assign_department:
            arrDepartment.append(department.id)

        return self._get_user().id in arrDepartment


    @api.multi
    def _get_compare_hr(self):
        #comparing HR Jobs
        arrJobs = []

        jobs = self.env['hr.job'].search([('id','=',self._get_employee().job_id.id)]).id
        jobs_compare_hr = self.env['hr.job'].search([('name','in',['HR','hr','HR & GA Head Assistant',
                                                                   'hr & GA  Head Assistant',
                                                                   'Administration Assistant','KTU','ktu'])])
        for record_job in jobs_compare_hr:
            arrJobs.append(record_job.id)

        return jobs in arrJobs

    @api.multi
    def _get_compare_non_hr(self):
        #Non Comparing Hr Jobs
        arrJobs2 = []

        jobs = self.env['hr.job'].search([('id','=',self._get_employee().job_id.id)]).id
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
        assign_division= self.env['res.groups'].search([('name','like',self.purchase_request_division_head())]).users
        technic3 = self.env['res.groups'].search([('name','like',self.purchase_request_technical3())]).users
        technic4 = self.env['res.groups'].search([('name','like',self.purchase_request_technical4())]).users
        technic5 = self.env['res.groups'].search([('name','like',self.purchase_request_technical5())]).users
        budget = self.env['res.groups'].search([('name','like',self.purchase_request_budget())]).users
        director= self.env['res.groups'].search([('name','like',self.purchase_request_director())]).users
        president_director = self.env['res.groups'].search([('name','like',self.purchase_request_president_director())]).users
        ro_head = self.env['res.groups'].search([('name','like',self.purchase_ro_head())]).users

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

    @api.multi
    def action_financial_approval1(self):
        """ Confirms department Head Financial Approval.
        """
        if self._get_max_price() < self._get_price_low():
            self.button_approved()
        elif self._get_max_price() >= self._get_price_low():
            state_data = {'state':'approval4','assigned_to':self._get_division_finance()}
            self.write(state_data)

    @api.multi
    def action_financial_approval2(self):
        """ Confirms Division Head Financial Approval.
        """
        if self._get_max_price() < self._get_price_mid():
                self.button_approved()
        elif self._get_max_price() >= self._get_price_mid():
            state_data = {'state':'approval5','assigned_to' : self._get_director()}
            self.write(state_data)

    @api.multi
    def action_financial_approval3(self):
        """ Confirms Director  Financial Approval.
        """
        if self._get_max_price() < self._get_price_high():
                self.button_approved()
        elif self._get_max_price() >= self._get_price_high():
            state_data = {'state':'approval6','assigned_to' : self._get_president_director()}
            self.write(state_data)

    @api.multi
    def action_financial_approval4(self):
        """ Confirms President Director Approval.
        """
        self.button_approved()

    @api.multi
    def button_approved(self):
        self.tracking_approval()
        self.create_purchase_requisition()
        self.create_quotation_comparison_form()
        super(InheritPurchaseRequest, self).button_approved()
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
        jobs_compare_hr = self.env['hr.job'].search([('name','in',['Budgeting','budget','budgeting','Budget'])]).id
        employeemanager = self.env['hr.employee'].search([('job_id','=',jobs_compare_hr)]).user_id.id
        self.write({'state': 'budget','assigned_to':employeemanager})

    @api.multi
    def action_budget(self,):
        """ Confirms Budget request.
        """
        state_data = []
        if self.type_budget== 'not' and not self.pta_code:
            raise exceptions.ValidationError('Input Your PTA Number')
        elif self.type_functional == 'general' and self.department_id.code in ['GA','FIN','GIS','ACC','LGL','HR','SPC','CSR']and self._get_max_price() < self._get_price_low():
            self.button_approved()
        else:
            try:
               if self.type_functional == 'agronomy' and self._get_max_price() < self._get_price_low() or self.type_functional == 'agronomy' and self._get_max_price() >= self._get_price_low():
                    state_data = {'state':'technic4','assigned_to':self._get_technic_agronomy()}
               elif self.type_functional == 'technic' and self._get_max_price() < self._get_price_low() or self.type_functional == 'technic' and self._get_max_price() >= self._get_price_low():
                    state_data = {'state':'technic5','assigned_to':self._get_technic_ie()}
               elif self.type_functional == 'general' and self.department_id.code not in ['GA','FIN','GIS','ACC','LGL','HR','SPC','CSR']and self._get_max_price() < self._get_price_low() or self.type_functional == 'general' and self.department_id.code not in ['GA','FIN','GIS','ACC','LGL','HR','SPC','CSR'] and self._get_max_price() >= self._get_price_low() :
                    state_data = {'state':'technic3','assigned_to':self._get_technic_ict()}
               elif self.type_functional == 'general' and self.department_id.code in ['GA','FIN','GIS','ACC','LGL','HR','SPC','CSR'] and self._get_max_price() >= self._get_price_low() :
                    state_data = {'state':'approval4','assigned_to':self._get_division_finance()}
            except:
                raise exceptions.ValidationError('Call Your Hr Admin to Fill Department Code')
            self.write(state_data)

    @api.multi
    def action_technic(self):
        """ Confirms Technical request.
        """
        state_data = []

        if self._get_compare_hr() and self.type_functional != 'technic' and self._get_max_price() < self._get_price_low():
            state_data = {'state':'approval3','assigned_to':self._get_user_agronomy()}
        elif self._get_compare_hr() and self.type_functional == 'technic' and self._get_max_price() < self._get_price_low():
            state_data = {'state':'approval3','assigned_to':self._get_technic_ie}
        elif self._get_compare_hr() and self._get_max_price() >= self._get_price_low() or self._get_compare_non_hr():
            state_data = {'state':'approval4','assigned_to':self._get_division_finance()}
        else:
            raise exceptions.ValidationError('Call Your Hr Admin to fill Your Jobs')

        self.write(state_data)

    @api.model
    def create(self, vals):
        vals['name']=self.env['ir.sequence'].next_by_code('purchase.request.seq')
        request = super(InheritPurchaseRequest, self).create(vals)
        return request

    @api.multi
    def check_wkf_requester(self):
        #checking Approval Requester
        state_data = []

        if self._get_compare_hr():
            self.write({'state':'confirm'})
            state_data = {'state':'approval7','assigned_to':self._get_user_ro_manager()}

        elif self._get_compare_non_hr():
            self.write({'state':'confirm'})
            state_data = {'state':'approval1','assigned_to':self._get_user_manager()}

        else:
            raise exceptions.ValidationError('Call Your Hr Admin to fill Your Jobs')

        self.write(state_data)

    @api.multi
    def action_ro_head_approval(self):
        #Action Approval RO Head
        state_data = []

        if self._get_max_price() >= self._get_price_low():
            state_data = {'state':'approval2','assigned_to':self._get_division_finance()}
        elif self.type_functional == 'agronomy' and self._get_max_price() < self._get_price_low() :
            state_data = {'state':'technic4','assigned_to':self._get_technic_agronomy()}
        elif self.type_functional == 'technic' and self._get_max_price() < self._get_price_low():
            state_data = {'state':'technic5','assigned_to':self._get_technic_ie()}
        elif self.type_functional == 'general' and self._get_max_price() < self._get_price_low():
            state_data = {'state':'technic3','assigned_to':self._get_technic_ict()}
        else:
            raise exceptions.ValidationError('Call Your Procurement Admin To Set Rule of Price')

        self.write(state_data)

    @api.multi
    def check_wkf_product_price(self):
       #check total product price in purchase request
       state_data = []

       if self._get_max_price() >= self._get_price_low() and self._get_employee().parent_id.id:
            state_data = {'state':'approval2','assigned_to':self._get_employee().parent_id.id}
       elif self._get_max_price() >= self._get_price_low() and not self._get_employee().parent_id.id or self.type_functional == 'agronomy' and self._get_max_price() < self._get_price_low() or self.type_functional == 'technic' and self._get_max_price() < self._get_price_low() or self.type_functional == 'general' and self._get_max_price() < self._get_price_low() :
            state_data = {'state':'budget','assigned_to':self._get_budget_manager()}
       else:
            raise exceptions.ValidationError('Call Your Procurement Admin To Set Rule of Price')

       self.write(state_data)

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

        for purchaseline in self.env['purchase.request.line'].search([('request_id.id','=',self.id)]):
            purchaseline_data = {
                'product_id': purchaseline.product_id.id,
                'product_uom_id': purchaseline.product_uom_id.id,
                'product_qty' : purchaseline.product_qty,
                'requisition_id' : res.id
            }
            self.env['purchase.requisition.line'].create(purchaseline_data)

        return True

    @api.multi
    def create_quotation_comparison_form(self):
        purchase_requisition = self.env['purchase.requisition'].search([('origin','like',self.complete_name)])
        purchase_data = {
                'company_id': purchase_requisition.companys_id.id,
                'date_pp': datetime.today(),
                'requisition_id': purchase_requisition.id,
                'origin' : purchase_requisition.origin,
                'type_location' : purchase_requisition.type_location,
                'location':purchase_requisition.location
            }
        res = self.env['quotation.comparison.form'].create(purchase_data)

    @api.multi
    @api.depends('assigned_to')
    def _change_validation_user(self):
        if self.assigned_to.id == self._get_user().id and self._check_departement_head and self.state == 'approval1':
            self.validation_user = True

    @api.depends('assigned_to')
    def _change_validation_finance(self):

        if self.assigned_to.id == self._get_user().id and self.state == 'approval3':
            self.validation_finance = True

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

            try :
                departement_code = self.department_id.code
            except:
                departement_code = self.department_id.name

            if self.department_id.code == False:
                raise exceptions.ValidationError('Department Code is Null')
            else:
                self.complete_name = self.name + '/' \
                                         + self.company_id.code+'-'\
                                         +'PP'+'/'\
                                         +departement_code+'/'+str(month)+'/'+str(year)
        else:
            self.complete_name = self.name

        return True

    @api.multi
    def print_purchase_request(self):
        return self.env['report'].get_action(self, 'purchase_indonesia.report_purchase_request')

    @api.multi
    @api.depends('line_ids')
    def _compute_total_estimate_price(self):
        self.total_estimate_price = sum(record.total_price for record in self.line_ids)

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
        if self.type_functional == 'agronomy':
            department = self.env['hr.department'].search([('name','in',['agronomi','Agronomi',
                                                                         'Agronomy','agronomy','PR & LA','Pr & La',
                                                                         'PR&LA','pr & la','pr&la'])])
            for department in department:
                arrDepartment.append(department.id)
            return {
                'domain':{
                    'department_id':[('id','in',arrDepartment)]
                }
            }
        if self.type_functional == 'technic':
            department = self.env['hr.department'].search([('name','in',['IE','transport & workshop','Transport & Workshop'])])
            for department in department:
                arrDepartment.append(department.id)
            return {
                'domain':{
                    'department_id':[('id','in',arrDepartment)]
                }
            }
        if self.type_functional == 'general':
            department = self.env['hr.department'].search([('name','in',['HR & GA','HR','GA',
                                                                         'ICT','Finance','Legal','Procurement','GIS','RO'])])
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
    @api.constrains('line_ids')
    def _constrains_product__purchase_request_id(self):
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


class InheritPurchaseRequestLine(models.Model):

    _inherit = 'purchase.request.line'
    _description = 'Inherit Purchase Request Line'

    @api.multi
    @api.depends('product_id', 'name', 'product_uom_id', 'product_qty',
                 'analytic_account_id', 'date_required', 'specifications')
    def _compute_is_editable(self):
        for rec in self:
            if rec.request_id.state != 'draft':
                rec.is_editable = False
            else:
                rec.is_editable = True

    price_per_product = fields.Float('Prod Price',compute='_compute_price_per_product')
    total_price = fields.Float('Total Price',compute='_compute_total_price')
    budget_available = fields.Float('Budget Available')
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
    @api.depends('product_id')
    def _compute_price_per_product(self):
        for item in self:
            if item.product_id:
                product_temp = item.env['product.price.history'].search([('product_id','=',item.product_id.id)])
                price = max(producttemp.cost for producttemp in product_temp)
                item.price_per_product = price

    @api.multi
    @api.onchange('analytic_account_id')
    def _onchange_budget_available(self):
        arrBudget = []
        if self.analytic_account_id:
            budget = self.env['crossovered.budget.lines'].search([('analytic_account_id','=',self.analytic_account_id.id)])
            for budget in budget:
                arrBudget.append(budget.planned_amount)
            for amount in arrBudget:
                amount = float(amount)
                self.budget_available = amount

    @api.multi
    @api.onchange('request_id','product_id')
    def _onchange_product_purchase_request_line(self):
        #use to onchange domain product same as product_category
        if self.request_id.type_functional and self.request_id.department_id:
            arrProductCateg = []
            mappingFuntional = self.env['mapping.department.product'].search([('type_functional','=',self.request_id.type_functional),
                                                                              ('department_id.id','=',self.request_id.department_id.id)])
            for productcateg in mappingFuntional:
                arrProductCateg.append(productcateg.product_category_id.id)
            arrProdCatId = []
            prod_categ = self.env['product.category'].search([('parent_id','in',arrProductCateg)])
            for productcategparent in prod_categ:
                arrProdCatId.append(productcategparent.id)
            if prod_categ:
                return  {
                    'domain':{
                        'product_id':[('categ_id','in',arrProdCatId)]
                         }
                    }
            elif prod_categ != ():
                return  {
                    'domain':{
                        'product_id':[('categ_id','in',arrProductCateg)]
                         }
                    }






