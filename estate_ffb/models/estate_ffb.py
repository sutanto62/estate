from openerp import models, fields, api, exceptions
import openerp.addons.decimal_precision as dp

class EstateFFB(models.Model):
    
    _name = 'estate.ffb'
    _description = 'Fresh Fruit Bunches'
    _inherit=['mail.thread']
    
    name = fields.Char("Name", required=True, store=True, default='New')
    date = fields.Date("Date", default=fields.Date.context_today, required=True)
    clerk_id = fields.Many2one('hr.employee', string="Clerk", required=True)  # constrains: if team_id.assistant_id = true
    team_ids = fields.Many2many('estate.hr.team', string="Team", required=True)
    team_member_ids = fields.One2many('estate.hr.member',  
                                      domain="[('team_id', 'in', team_ids)]", store=False)
    estate_id = fields.Many2one('stock.location', "Estate",
                                domain=[('estate_location', '=', True), ('estate_location_level', '=', '1'),
                                ('estate_location_type', '=', 'planted')],required=True)
    company_id = fields.Many2one('res.company', 'Company', help='Define location company.', required=True)
    division_id = fields.Many2one('stock.location', "Division", required=True,
                                  domain=[('estate_location', '=', True), ('estate_location_level', 'in', ['1','2'])])
    approver_id = fields.Many2one('hr.employee', "Agronomy Assistant", required=True)  # constrains: if team_id.assistant_id = true
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('approved', 'Approved'),
                              ('rejected', 'Rejected')], "State", default="draft", track_visibility="onchange")
    description = fields.Text("Description")
    ffb_detail_ids = fields.One2many('estate.ffb.detail', string='FFB Line', inverse_name='ffb_id')
    
class EstateFFBDetail(models.Model):
    
    _name = 'estate.ffb.detail'
    _description = 'Fresh Fruit Bunches Detail'
    _inherit=['mail.thread']
    
    ffb_id = fields.Many2one('estate.ffb', string='FFB', ondelete='cascade')
    upkeep_date = fields.Date(related='ffb_id.date', string='Date', store=True)
    employee_id = fields.Many2one('hr.employee', 'Harvester', required=True, track_visibility='onchange',
                                  domain=[('contract_type', 'in', ['1', '2'])])
    employee_nik = fields.Char(related='employee_id.nik_number', string="Employee Identity Number ", store=True)
    employee_company_id = fields.Many2one(related='employee_id.company_id', string='Employee Company', store=True,
                                          help="Company of employee")
    division_id = fields.Many2one(related='ffb_id.division_id', string='Division',
                            help='Define division of employee.', compute="_compute_division")
    tph_id = fields.Many2one('estate.block.template', 'TPH',
                                  domain="[('inherit_location_id.location_id.location_id.location_id', '=', division_id)]")
    block_id = fields.Many2one(related='tph_id.inherit_location_id.location_id.location_id', string='Block', store=True,
                            help='Define block of tph.')
    location_id = fields.Many2one('estate.block.template', 'Location', store=True)
    planted_year_id = fields.Many2one(related='location_id.planted_year_id', 
                                      string='Planted Year', store=True)
    qty_n = fields.Float('Ripe (N)', track_visibility='onchange',
                                       help='Define ripe ffb', digits=dp.get_precision('Product Unit of Measure'))
    qty_a = fields.Float('Unripe (A)', track_visibility='onchange',
                                       help='Define unripe ffb', digits=dp.get_precision('Product Unit of Measure'))
    qty_e = fields.Float('Overripe (E)', track_visibility='onchange',
                                       help='Define overripe ffb', digits=dp.get_precision('Product Unit of Measure'))
    qty_l = fields.Float('Long Stalk (L)', track_visibility='onchange',
                                       help='Define long stalk ffb', digits=dp.get_precision('Product Unit of Measure'))
    qty_b = fields.Float('Loose Fruit (B)', track_visibility='onchange',
                                       help='Define loose ffb', digits=dp.get_precision('Product Unit of Measure'))
    flag_s = fields.Boolean('Not Stacked (S)', track_visibility='onchange',
                                       help='Define not stacked status ffb')
    flag_k = fields.Boolean('Not on Sack (K)', track_visibility='onchange',
                                       help='Define not on sack status ffb')
    
    @api.one
    def _compute_division(self):
        """Define location domain while editing record
        """
        self.division_id = self.ffb_id.division_id
        
    @api.onchange('tph_id')
    def _onchange_tph_id(self):
        """Define location domain while editing record
        """
        block = self.env['estate.block.template'].search([('inherit_location_id', '=', self.tph_id.inherit_location_id.location_id.location_id.id)])
        if len(block):
            self.location_id = block[0]