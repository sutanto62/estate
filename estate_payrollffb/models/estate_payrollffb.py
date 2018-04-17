# -*- coding: utf-8 -*-
from datetime import datetime
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

class EstatePayrolFFB(models.Model):
    """
    Team activity records. It record harvest labour activity.
    """
    _name = 'estate.payrollffb'
    _description = 'Payroll FFB'
    _inherit=['mail.thread']
    
    def get_date_number(self, str_date):
        date_date = datetime.strptime(str_date, '%Y-%m-%d')
        return date_date.weekday()
    
    def get_is_holiday(self, str_date):
        #implementation of is holiday day, currently is for sunday 6
        #should be able to get public holiday too
        return self.get_date_number(self.date) == 6
    
    def get_is_friday(self, str_date):
        return self.get_date_number(self.date) == 4
    
    name = fields.Char("Name", required=True, store=True, default='New')
    date = fields.Date("Date", default=fields.Date.context_today, required=True)
    max_day = fields.Integer("Date Constraint", help='Change to override maximum harvest date day(s) configuration')
    date_number = fields.Integer("Date Number", compute='_compute_date', store=False)
    is_friday = fields.Boolean("Friday", compute='_compute_is_friday', store=False)
    is_holiday = fields.Boolean("Holiday", compute='_compute_is_holiday', store=False)
    team_id = fields.Many2one('estate.hr.team', "Team", required=True)
    team_member_ids = fields.One2many(related='team_id.member_ids', string='Member', store=False)
    estate_id = fields.Many2one('stock.location', "Estate",
                                domain=[('estate_location', '=', True), ('estate_location_level', '=', '1'),
                                ('estate_location_type', '=', 'planted')],required=True)
    company_id = fields.Many2one('res.company', 'Company', help='Define location company.', required=True)
    division_id = fields.Many2one('stock.location', "Division", required=True,
                                  domain=[('estate_location', '=', True), ('estate_location_level', 'in', ['1','2'])])
    approver_id = fields.Many2one('hr.employee', "Approver")  # constrains: if team_id.assistant_id = true
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('agr_asst_approved', 'Agronomy Assistant Approved'),
                              ('agr_head_approved', 'Agronomy Head Assistant Approved'),
                              ('estate_mgr_approved', 'Estate Manager Approved'),
                              ('approved', 'Full Approved'),
                              ('rejected', 'Rejected')], "State", default="draft", track_visibility="onchange")
    description = fields.Text("Description")
    labour_line_ids = fields.One2many('estate.payrollffb.labour', string='Harvest Labour', inverse_name='payrollffb_id')
    ffb_detail_amount = fields.Char('Harvester Total', compute='_compute_ffb_detail_count', store=False)
    upkeep_labour_lines = fields.Integer('Upkeep labour Amount', compute='_compute_upkeep_labour_lines')
    
    def _compute_date(self):
        self.date_number = self.get_date_number(self.date)
    
    def _compute_is_friday(self):
        self.is_friday = self.get_is_friday(self.date)
    
    def _compute_is_holiday(self):
        self.is_holiday = self.get_is_holiday(self.date)

    def _compute_ffb_detail_count(self):
        ffb_detail_ids = self.env['estate.ffb.detail'].search([('upkeep_date', '=', self.date), ('team_id', '=', self.team_id.id)])
        employee_ids = []
        tph_ids = []
        for rec in ffb_detail_ids:
            employee_ids.append(rec.employee_id.id)
            tph_ids.append(rec.tph_id.id)
        self.ffb_detail_amount = str(len(set(employee_ids))) + ' / ' + str(len(set(tph_ids)))

    @api.multi
    def _compute_upkeep_labour_lines(self):
        for rec in self:
            labour_lines_ids = rec.env['estate.upkeep.labour'].search([('upkeep_team_id', '=', rec.team_id.id),
                                                                        ('upkeep_date', '=', rec.date)])
            employee_ids = []
            for line in labour_lines_ids:
                employee_ids.append(line.employee_id.id)
            self.upkeep_labour_lines = len(set(employee_ids))

    @api.constrains('date')
    def _check_date(self):
        """
        Harvest Labour date should be limited. Didn't support different timezone
        Condition:
        1. Zero value of max entry day = today transaction should be entry today.
        2. Positive value of max entry day = allowed back/future dated transaction.
        """
        if self.date:
            fmt = '%Y-%m-%d'
            d1 = datetime.strptime(self.date, fmt)
            d2 = datetime.strptime(fields.Date.today(), fmt)
            delta = (d2 - d1).days
            if self.max_day == 0 and abs(delta) > self.max_day:
                error_msg = _("Transaction date should be today")
                raise ValidationError(error_msg)
            elif self.max_day != 0 and abs(delta) > self.max_day:
                error_msg = _("Transaction date should not be less than/greater than or equal to %s day(s)" % self.max_day)
                raise ValidationError(error_msg)
            else:
                return True

    @api.constrains('team_id')
    def _check_team_id(self):
        """ Check each employee in estate.payrollffb.details is the correct team member.
        Check each LHMP with current date is for single team_id. """
        self.check_employee_membership()
        self.check_team_id_daily_payrollffb()

        return True

    @api.constrains('labour_line_ids')
    def _check_labour_line_ids_team_id(self):
        """ Check each employee in estate.payrollffb.details is the correct team member. """
        self.check_employee_membership()
        self.check_attendance_code_id()
        return True

    @api.model
    def create(self, vals):
        """ Get sequence number for estate.payrollffb"""
        if vals.get('name', 'New') == 'New':
            seq_obj = self.env['ir.sequence']
            estate_name = self.env['stock.location'].search([('id', '=', vals['estate_id'])])

            vals['name'] = seq_obj.with_context(ir_sequence_code_1=estate_name.name,
                                                ir_sequende_date=vals['date']).next_by_code('estate.payrollffb') or '/'

        return super(EstatePayrolFFB, self).create(vals)

    @api.multi
    def action_open_harvester_summary(self):
        for rec in self:
            rec = rec.with_context(search_default_filter_new=0,
                                   search_default_filter_month=1,
                                   search_default_by_date=1,
                                   search_default_by_team=1,
                                   search_default_by_harvester=1,
                                   search_default_by_block=1,
                                   search_default_by_tph=1,
                                   pivot_measures=['qty_n', 'qty_a', 'qty_e', 'qty_l', 'qty_b']
                                   )
            context = rec._context.copy()
            view_id = rec.env.ref('estate_ffb.estate_ffb_detail_view_tree').id
            summary_ids = rec.env['estate.ffb.detail'].search([('team_id', '=', rec.team_id.id),
                                                               ('upkeep_date', '=', rec.date)]).ids
            res = {
                'name': _('Harvester Summary Records Team %s' % self.team_id.name),
                'view_type': 'form',
                'view_mode': 'tree,pivot',
                'views': [(view_id, 'pivot')],
                'res_model': 'estate.ffb.detail',
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'context': context,
                'domain': [('id', '=', summary_ids)],
            }
            return res

    @api.multi
    def action_open_upkeep_labour(self):
        for rec in self:
            rec = rec.with_context(search_default_filter_new=0,
                                   search_default_by_team=1,
                                   search_default_by_employee=1,
                                   )
            context = rec._context.copy()
            view_id = rec.env.ref('estate.upkeep_labour_view_tree').id
            line_ids = rec.env['estate.upkeep.labour'].search([('upkeep_team_id', '=', rec.team_id.id),
                                                                ('upkeep_date', '=', rec.date)]).ids
            res = {
                'name': _('Upkeep Labour Records Team %s' % self.team_id.name),
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(view_id, 'tree')],
                'res_model': 'estate.upkeep.labour',
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'context': context,
                'domain': [('id', '=', line_ids)],
            }
            return res

    def check_employee_membership(self):
        """ Check sum of employee in selected team vs employee on harvest labour details """

        if self.labour_line_ids:
            employee_ids = []
            for record in self.labour_line_ids:
                employee_ids.append(record.employee_id.id)

            hr_member_ids = self.env['estate.hr.member'].search([('employee_id', 'in', employee_ids),
                                                                 ('team_id', '=', self.team_id.id)])
            member_ids = map(lambda i: i.employee_id.id, hr_member_ids)

            if not set(employee_ids) == set(member_ids):
                error_msg = _("Each employee should be the member of the selected team.")
                raise ValidationError(error_msg)

        return True

    def check_team_id_daily_payrollffb(self):
        """ Check each Daily Harvest Labour Sheet for each team per days """
        payrollffb_ids = self.search([('date', '=', self.date), ('team_id', '=', self.team_id.id)]).ids

        if len(payrollffb_ids) > 1:
            error_msg = _("Daily Payroll FFB Labour Sheet with current Team is already created today.")
            raise ValidationError(error_msg)

        return True

    def check_attendance_code_id(self):
        """ Check attendance code. Max attendace is 1 workdays """
        if self.labour_line_ids:
            for rec in self.labour_line_ids:
                total_ratio_day = sum(a.attendance_code_id.qty_ratio for a in self.labour_line_ids
                                      if a.employee_id.id == rec.employee_id.id)

                if total_ratio_day > 1:
                    error_msg = _("Total worked day of %s should not more than 1 worked day" % rec.employee_id.name_related)
                    raise ValidationError(error_msg)
                    break
                
    @api.one
    def sync_upkeep(self):
        #create estate.upkeep.activity
        harvest_activity_obj = self.env['estate.ffb.activity']
        FFB_ACTIVITY_ID, LOOSEFRUIT_ACTIVITY_ID = None, None
        
        try:
            FFB_ACTIVITY_ID = harvest_activity_obj.search([('activity_type', '=', 'panen_janjang')]).activity_id.id
            LOOSEFRUIT_ACTIVITY_ID = harvest_activity_obj.search([('activity_type', '=', 'panen_brondolan')]).activity_id.id
        except:
            error_msg = _("Cannot continue the process, please setting activity of harvest.")
            raise ValidationError(error_msg)
        
        estate_upkeep_activity_obj = self.env['estate.upkeep.activity']
        activity_obj = self.env['estate.activity']
        
        ffb_activity_id = activity_obj.browse(FFB_ACTIVITY_ID)
        loosefruite_activity_id = activity_obj.browse(LOOSEFRUIT_ACTIVITY_ID)
        
        #create estate.upkeep
        estate_upkeep_obj = self.env['estate.upkeep']
        vals_estate_upkeep = {
                              'assistant_id'        : self.team_id.assistant_id.id,
                              'team_id'             : self.team_id.id,
                              'date'                : self.date,
                              'estate_id'           : self.estate_id.id,
                              'max_day'             : self.max_day,
                              'company_id'          : self.company_id.id,
                              'division_id'         : self.division_id.id,
                              'state'               : 'draft',
                              'is_harvest'          : True
                            }
        upkeep_id = estate_upkeep_obj.create(vals_estate_upkeep)
        
        location_ids = []
        for labour in self.labour_line_ids:
            location_ids.append(labour.location_id.id)
        
        unit_amount = 1000
        vals_activity_ffb = {
                    'upkeep_id'             : upkeep_id.id,
                    'activity_id'           : ffb_activity_id.id,
                    'location_ids'          : location_ids,
                    'division_id'           : self.division_id.id,
                    'unit_amount'           : unit_amount
                    }
        estate_upkeep_activity_obj.create(vals_activity_ffb)
        
        vals_activity_loose_fruit = {
                    'upkeep_id'             : upkeep_id.id,
                    'activity_id'           : loosefruite_activity_id.id,
                    'location_ids'          : location_ids,
                    'division_id'           : self.division_id.id,
                    'unit_amount'           : unit_amount
                    }
        estate_upkeep_activity_obj.create(vals_activity_loose_fruit)
        
        #create estate.upkeep.labour
        for labour in self.labour_line_ids:
            labour.sync_upkeep(upkeep_id)
    
    @api.one            
    def action_sync(self):
        self.sync_upkeep()

class EstatePayrollffbLabour(models.Model):
    
    _name = 'estate.payrollffb.labour'
    _description = 'Payroll FFB Labour'
    _inherit=['mail.thread']
    
    payrollffb_id = fields.Many2one('estate.payrollffb', string='Payroll FFB Labour', ondelete='cascade')
    date = fields.Date(related='payrollffb_id.date', string='Date', store=True)
    employee_id = fields.Many2one('hr.employee', 'Harvester', required=True, track_visibility='onchange',
                                  domain=[('contract_type', 'in', ['1', '2'])])
    employee_nik = fields.Char(related='employee_id.nik_number', string="Employee Identity Number ", store=True)
    employee_company_id = fields.Many2one(related='employee_id.company_id', string='Employee Company', store=True,
                                          help="Company of employee")
    division_id = fields.Many2one(related='location_id.inherit_location_id', string='Division',
                            help='Define division of employee.')
    attendance_code_id = fields.Many2one('estate.hr.attendance', 'Attendance', track_visibility='onchange',
                                    help='Any update will reset employee\'s timesheet')
    attendance_code_ratio = fields.Float('Ratio', digits=(4,2), related='attendance_code_id.qty_ratio')
    location_id = fields.Many2one('estate.block.template', 'Location', store=True)
    planted_year_id = fields.Many2one(related='location_id.planted_year_id', 
                                      string='Planted Year', store=True)
    qty_ffb = fields.Float('Qty FFB', track_visibility='onchange',
                                       help='Define quantity FFB', digits=(4,0))
    qty_loose_ffb = fields.Float('Qty Loose FFB', track_visibility='onchange',
                                       help='Define quantity loose FFB', digits=(4,0))
    qty_penalty = fields.Float('Penalty', track_visibility='onchange',
                                       help='Define penalty', digits=(4,0))
    cross_team = fields.Boolean('Cross Team Activity', default=False,
                                help='Cross Team (CT). Check to open all locations.')

    @api.onchange('location_id','cross_team')
    def _onchange_location_id(self):
        """ Change block selection based on cross_team flag value"""
        if not self.cross_team or self.cross_team == None:
            stock_location_ids = self.env['stock.location'].search([
                                                            ('location_id', '=', self.payrollffb_id.division_id.id)]).ids
            return {
                'domain': {
                    'location_id': [('inherit_location_id', 'in', stock_location_ids)]
                }
            }

        else:
            stock_location_ids = self.env['stock.location'].search([]).ids
            return {
                'domain': {
                    'location_id': [('inherit_location_id', 'in', stock_location_ids)]
                }
            }

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """
        Define harvesting employee based on selected team_id.
        """
        team_id = self.payrollffb_id.team_id.id
        current_worker = []
        if team_id:
            hr_member_ids = self.env['estate.hr.member'].search([('team_id', '=', team_id)])
            for member in hr_member_ids:
                current_worker.append(member.employee_id.id)
            return {
                'domain': {'employee_id': [('id', 'in', current_worker)]}
            }
            
    def sync_upkeep(self, estate_upkeep_id):
        """
        Create upkeep labour to upkeep_id given
        """
        harvest_activity_obj = self.env['estate.ffb.activity']
        FFB_ACTIVITY_ID, LOOSEFRUIT_ACTIVITY_ID = None, None

        try:
            FFB_ACTIVITY_ID = harvest_activity_obj.search(
                [('activity_type', '=', 'panen_janjang')]).activity_id.id
            LOOSEFRUIT_ACTIVITY_ID = harvest_activity_obj.search(
                [('activity_type', '=', 'panen_brondolan')]).activity_id.id
        except:
            error_msg = _("Cannot continue the process, please setting activity of harvest.")
            raise ValidationError(error_msg)

        activity_obj = self.env['estate.activity']
        estate_upkeep_labour_obj = self.env['estate.upkeep.labour']
        estate_ffb_weight_id = self.env['estate.ffb.weight'].current()
        estate_ffb_yield_obj = self.env['estate.ffb.yield']
        
        ffb_activity_id = activity_obj.browse(FFB_ACTIVITY_ID)
        loosefruite_activity_id = activity_obj.browse(LOOSEFRUIT_ACTIVITY_ID)
        
        if ffb_activity_id and estate_upkeep_id and loosefruite_activity_id:
            
            bjr = estate_ffb_yield_obj.search([
                                        ('ffb_weight_id', '=', estate_ffb_weight_id.id),
                                        ('location_id', '=', self.location_id.id)
                                        ])

            if len(bjr) == 0:
                error_msg = _("The block %s's standard Average Weight Bunch is not configured." %( self.location_id.name))
                raise ValidationError(error_msg)

            kg_per_jjg = bjr.qty_ffb_base_kg/bjr.qty_ffb_base_jjg
            quantity = self.qty_ffb * kg_per_jjg
            quantity_piece_rate = (self.qty_ffb - bjr.qty_ffb_base_jjg if self.qty_ffb - bjr.qty_ffb_base_jjg > 0 else 0) * kg_per_jjg 
            
            vals_ffb = {
                'upkeep_id'             : estate_upkeep_id.id,
                'employee_id'           : self.employee_id.id,
                'activity_id'           : ffb_activity_id.id,
                'location_id'           : self.location_id.id,
                'attendance_code_id'    : self.attendance_code_id.id,
                'quantity'              : quantity,
                'quantity_piece_rate'   : quantity_piece_rate,
                'number_of_day'         : self.attendance_code_id.qty_ratio,
                'qty_jjg'               : self.qty_ffb,
                'qty_jjg_basis'         : bjr.qty_ffb_base_jjg,
            }
            estate_upkeep_labour_obj.create(vals_ffb)
            
            if self.qty_loose_ffb > 0:
                quantity = self.qty_loose_ffb
                vals_loose_fruite = {
                    'upkeep_id'             : estate_upkeep_id.id,
                    'employee_id'           : self.employee_id.id,
                    'activity_id'           : loosefruite_activity_id.id,
                    'location_id'           : self.location_id.id,
                    'quantity'              : quantity,
                }
                estate_upkeep_labour_obj.create(vals_loose_fruite)