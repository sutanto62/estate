from openerp import models, fields
from datetime import datetime

class EstateFFBPayroll(models.Model):
    """
    Team activity records. It record harvest labour activity.
    """
    _name = 'estate.harvest'
    _description = 'Daily Harvest'
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
    harvest_labour_ids = fields.One2many('estate.harvest.labour', string='Harvest Labour', inverse_name='harvest_id')
    
    def _compute_date(self):
        self.date_number = self.get_date_number(self.date)
    
    def _compute_is_friday(self):
        self.is_friday = self.get_is_friday(self.date)
    
    def _compute_is_holiday(self):
        self.is_holiday = self.get_is_holiday(self.date)
    
class EstateFFBPayrollLabour(models.Model):
    
    _name = 'estate.harvest.labour'
    _description = 'Daily Harvest Detail'
    _inherit=['mail.thread']
    
    harvest_id = fields.Many2one('estate.harvest', string='Daily Harvest', ondelete='cascade')
    harvest_date = fields.Date(related='harvest_id.date', string='Date', store=True)
    employee_id = fields.Many2one('hr.employee', 'Harvester', required=True, track_visibility='onchange',
                                  domain=[('contract_type', 'in', ['1', '2'])])
    employee_nik = fields.Char(related='employee_id.nik_number', string="Employee Identity Number ", store=True)
    employee_company_id = fields.Many2one(related='employee_id.company_id', string='Employee Company', store=True,
                                          help="Company of employee")
    division_id = fields.Many2one(related='harvest_id.division_id', string='Division',
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
    
#     @api.one
#     def _compute_division(self):
#         """Define location domain while editing record
#         """
#         self.division_id = self.harvest_id.division_id