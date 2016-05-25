# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

estate_working_days = 25 # todo create working calendar
overtime_amount = 10000

class AccountAnalyticAccount(models.Model):
    """
    Domains for upkeep entry.
    """
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'
    _description = 'Analytic Account'

    use_estate = fields.Boolean('Estate', help="Check this field if this project manages estate")

class EstateBlockTemplate(models.Model):
    """
    Upkeep need daily costing
    """
    _inherit = 'estate.block.template'

    account_income_id = fields.Many2one('account.account', 'Income Account', domain=[('type', '=', 'other')])
    account_expense_id = fields.Many2one('account.account', 'Expense Account', domain=[('type', '=', 'other')])


class Upkeep(models.Model):
    """
    Team activity records. It record upkeep activity, labour and material usage.
    """
    _name = 'estate.upkeep'
    _order = 'date, team_id'

    name = fields.Char("Name", compute="_compute_upkeep_name", store=True)
    assistant_id = fields.Many2one('hr.employee', "Assistant", required=True)  # constrains: if team_id.assistant_id = true
    team_id = fields.Many2one('estate.hr.team', "Team", required=True)
    date = fields.Date("Date", default=fields.Date.context_today, required=True)
    description = fields.Text("Description")
    estate_id = fields.Many2one('stock.location', "Estate",
                                domain=[('estate_location', '=', True), ('estate_location_level', '=', '1'),
                                ('estate_location_type', '=', 'planted')])
    # constrains: limit to estate_id childs
    division_id = fields.Many2one('stock.location', "Division", required=True,
                                  domain=[('estate_location', '=', True), ('estate_location_level', '=', '2')])
    #material_ids = fields.One2many('estate.upkeep.material', inverse_name='upkeep_id')  # constrains: material_ids.product_id = activity_ids.product_id
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('approved', 'Approved'),
                              ('correction', 'Correction'),
                              ('payslip', 'Payslip Processed')], "State", default="draft")
    activity_line_ids = fields.One2many('estate.upkeep.activity', inverse_name='upkeep_id')
    labour_line_ids = fields.One2many('estate.upkeep.labour', inverse_name='upkeep_id')
    material_line_ids = fields.One2many('estate.upkeep.material', inverse_name='upkeep_id')
    comment = fields.Text('Additional Information')

    @api.one
    @api.depends('date', 'team_id')
    def _compute_upkeep_name(self):
        if self.date and self.team_id:
            self.name = 'BKM/' + self.date + '/' + self.team_id.name # todo add code with sequence number
        return True

    @api.one
    @api.onchange('team_id')
    def _onchange_team_id(self):
        """No need to entry Assistant
        """
        if self.team_id:
            if self.team_id.assistant_id:
                self.assistant_id = self.team_id.assistant_id
        return True

    @api.one
    @api.onchange('assistant_id')
    def _onchange_assistant_id(self):
        """No need to entry block (division level)
        :return: first block and set to division_id
        """
        if self.assistant_id:
            block = self.env['estate.block.template'].search([('assistant_id', '=', self.assistant_id.id)],
                                                             limit=1,
                                                             order='id')
            res = self.env['stock.location'].search([('id', '=', block.inherit_location_id.id)])
            if res:
                self.division_id = res
            return res

    @api.one
    @api.onchange('division_id')
    def _onchange_division_id(self):
        """Select estate automatically, Update location domain in upkeep line
        :return: first estate and set to estate_id
        """
        if self.division_id:
            res = self.env['stock.location'].search([('id', '=', self.division_id.location_id.id)])
            if res:
                self.estate_id = res

    @api.one
    @api.constrains('date')
    def _check_date(self):
        """Didn't support different timezone
        """
        config = self.env['estate.config.settings'].search([], order='id desc', limit=1)
        if self.date:
            fmt = '%Y-%m-%d'
            d1 = datetime.strptime(self.date, fmt)
            d2 = datetime.strptime(fields.Date.today(), fmt)
            delta = (d2 - d1).days
            if config.default_max_entry_day:
                if delta >= config.default_max_entry_day:
                    error_msg = "Transaction date should not be less than or equal to %s day(s)" % config.default_max_entry_day
                    raise exceptions.ValidationError(error_msg)
            else:
                return True

    @api.one
    @api.constrains('labour_line_ids')
    def _check_quantity(self):
        """Check total unit amount of labour equal or less than upkeep unit amount
        """
        if self.labour_line_ids:
            # Get unique labour's activity
            labour_activity = self.get_labour_activity()

            # Check amount activity unit amount
            for record in labour_activity:
                filter_activity = [('activity_id', '=', record), ('upkeep_id', 'in', self.ids)]
                labour_quantity = sum(line.quantity for line in self.labour_line_ids.search(filter_activity))
                upkeep_unit_amount = self.activity_line_ids.search(filter_activity).unit_amount
                activity = self.env['estate.activity'].search([('id', '=', record)]).name

                if labour_quantity > upkeep_unit_amount:
                    error_msg = "Total %s labour's amount should equal or less than %s" % (activity, upkeep_unit_amount)
                    raise exceptions.ValidationError(error_msg)
        return True

    @api.multi
    def get_activity(self):
        """Labour's activity should match with upkeep activity
        :return: activity
        """
        activity = []
        records = self.activity_line_ids
        for record in records:
            # Use complete name instead of name (name might be duplicate).
            activity.append(record.activity_id.complete_name)
        if len(activity):
            return activity
        return False

    @api.multi
    def get_labour(self, activity):
        labour = []
        records = self.labour_line_ids
        for record in records.search([('activity_id', '=', activity)]):
            labour.append(record.employee_id.name)
        if len(labour):
            return labour
        return False

    @api.multi
    def get_labour_activity(self):
        """Return set of labour's activity
        :return: list of activity or False
        """
        labour_line_activity = []
        for activity in self.labour_line_ids:
            labour_line_activity.append(activity.activity_id.id)
        if len(labour_line_activity):
            return set(labour_line_activity)
        return False

    @api.multi
    def get_labour_attendance(self, activity):
        """
        Return list of attendance code of activity
        :param activity: activity id
        :return: list of attendance code id or False
        """
        attendance = []
        for att in self.labour_line_ids.search([('activity_id', '=', activity),
                                                ('upkeep_id', 'in', self.ids)]):
            if att.attendance_code_id.id:
                attendance.append(att.attendance_code_id.id)
        if len(attendance):
            return set(attendance)

        return False

    @api.multi
    def calculate_labour_qty(self):
        """
        Help user to define each labour's work result which has an attendance code.
        Calculation will reset previous entry.
        """

        qty_ratio = 0.00

        # Get unique labour's activity
        labour_activity = self.get_labour_activity()

        # Calculate quantity per labour
        for activity_id in labour_activity:
            # qty_ratio = activity_qty/((att_ratio_1.lbr1)+(att_ratio_2.lbr2)+(att_ratio_x.lbrx))

            activity_qty = self.activity_line_ids.search([('activity_id', '=', activity_id),
                                                          ('upkeep_id', 'in', self.ids)], limit=1).unit_amount

            # get unique attendance code
            labour_attendance = self.get_labour_attendance(activity_id)

            if labour_attendance:
                attendance_amount_ratio = []
                for attendance_id in labour_attendance:
                    # get attendance code ratio
                    att_ratio = self.env['estate.hr.attendance'].search([('id', '=', attendance_id)], limit=1).qty_ratio
                    # count labour
                    filter_labour = [('activity_id', '=', activity_id),
                                     ('attendance_code_id', '=', attendance_id),
                                     ('upkeep_id', 'in', self.ids)]
                    labour_amount = len(self.labour_line_ids.search(filter_labour))
                    # calculate attendance amount ratio per attendance code
                    attendance_amount_ratio.append(att_ratio * labour_amount)

                # calculate quantity ratio
                qty_ratio = activity_qty/sum(attendance_amount_ratio)
                # Update labour quantity
                self.set_labour_qty(qty_ratio, activity_id)

        return True

    @api.one
    def button_confirmed(self):
        self.write({
            'state': 'confirmed'
        })

    @api.one
    def button_approved(self):
        """Create analytic journal entry
        """
        self.write({
            'state': 'approved'
        })

    @api.one
    def button_cancel(self):
        """Unlink analytic journal entry
        """
        state = ''
        if self.state == 'confirmed':
            state = 'draft'

        if self.state == 'approved':
            state = 'confirmed'

        self.write({
            'state': state
        })

    @api.multi
    def set_labour_qty(self, ratio, activity):
        """Update labour's unit amount
        """
        for record in self.labour_line_ids.search([('activity_id', '=', activity)]):
            record.quantity = record.attendance_code_ratio * ratio



class UpkeepActivity(models.Model):
    _name = 'estate.upkeep.activity'
    # _inherits = {'account.analytic.line': 'line_id'}

    name = fields.Char('Name', compute='_compute_name')
    upkeep_id = fields.Many2one('estate.upkeep', string='Upkeep', ondelete='cascade')
    upkeep_date = fields.Date(related='upkeep_id.date', store=True)
    # line_id = fields.Many2one('account.analytic.line', 'Analytic Line', ondelete='cascade', required=True),
    activity_id = fields.Many2one('estate.activity', 'Activity', domain=[('type', '=', 'normal')],
                                  help='Any update will reset Block.',
                                  required=True)
    activity_uom_id = fields.Many2one('product.uom', 'Unit of Measurement', related='activity_id.uom_id')

    location_ids = fields.Many2many('estate.block.template', id1='activity_id', id2='location_id',
                                    string='Location')
    division_id = fields.Many2one('stock.location', compute='_compute_division')
    unit_amount = fields.Float('Target Unit Amount', help="Calculate labour's work result by dividing with attendance ratio.") # constrains sum of labour activity quantity
    amount = fields.Float('Cost', compute='_compute_amount', store=True,
                          help='Sum of labour wage and material cost.')
    labour_unit_amount = fields.Float('Labour Unit Amount', compute='_compute_amount', store=True,
                                      help="Sum of labour's work result.")
    labour_number_of_day = fields.Float('Number of Day', compute='_compute_amount', store=True,
                                        help="Sum of activity's labour work day(s).")
    labour_piece_rate_amount = fields.Float('Piece Rate', compute='_compute_amount', store=True,
                                            help="Sum of activity's piece rate in same.")
    labour_overtime_amount = fields.Float('Over Time', compute="_compute_amount", store=True,
                                           help="Sum of activity's overtime.")
    labour_amount = fields.Float('Labour Wage', compute='_compute_amount',
                                 help="Sum of labour's wage.")
    material_amount = fields.Float('Material Cost', compute='_compute_amount',
                                   help="Sum of material's cost.")
    account_id = fields.Many2one('account.analytic.line', 'Analytic Account Line')
    comment = fields.Text('Remark')
    state = fields.Selection(related='upkeep_id.state')  # todo ganti dg context
    ratio_quantity_day = fields.Float('Ratio Quantity/Day', compute='_compute_ratio', store=True, group_operator="avg",
                                      help='Included piece rate conversion to number of day based on activity standard base')
    ratio_day_quantity = fields.Float('Ratio Day/Quantity', compute='_compute_ratio', store=True, group_operator="avg",
                                      help='Included piece rate conversion to number of day based on activity standard base')
    ratio_wage_quantity = fields.Float('Ratio Wage/Quantity', compute='_compute_ratio', store=True, group_operator="avg",
                                       help='Included piece rate conversion to number of day based on activity standard base')

    @api.multi
    @api.depends('activity_id')
    def _compute_name(self):
        for record in self:
            record.name = record.activity_id.name

    @api.one
    def _compute_division(self):
        """Define location domain while editing record
        """
        self.division_id = self.upkeep_id.division_id

    @api.one
    @api.depends('upkeep_id.labour_line_ids', 'upkeep_id.material_line_ids')
    def _compute_amount(self):
        """Cost of labour and material
        """
        upkeep_labour_sum = 0
        upkeep_material_sum = 0

        if self.upkeep_id.labour_line_ids:
            labour_cost = self.env['estate.upkeep.labour'].search([('upkeep_id', '=', self.upkeep_id.id),
                                                                   ('activity_id', '=', self.activity_id.id)])
            upkeep_labour_sum = sum(record.amount for record in labour_cost)
            self.labour_amount = upkeep_labour_sum

            # Upkeep activity should reflects sum of these
            self.labour_unit_amount = sum(record.quantity for record in labour_cost)
            self.labour_number_of_day = sum(record.number_of_day for record in labour_cost)
            self.labour_overtime_amount = sum(record.quantity_overtime for record in labour_cost)
            self.labour_piece_rate_amount = sum(record.quantity_piece_rate for record in labour_cost)

        if self.upkeep_id.material_line_ids:
            material_cost = self.env['estate.upkeep.material'].search([('upkeep_id', '=', self.upkeep_id.id),
                                                                       ('activity_id', '=', self.activity_id.id)])
            upkeep_material_sum = sum(record.amount for record in material_cost)

            # Upkeep activity should reflects sum of these
            self.material_amount = upkeep_material_sum

        self.amount = upkeep_labour_sum + upkeep_material_sum

    @api.multi
    @api.depends('upkeep_id')
    def _compute_ratio(self):
        """Measure productivity and cost based on quantity or piece rate.
        Precision, required piece rate conversion to day based on activity standard base
        1. Quantity/Day, number of work result per day.
        2. Day/quantity, number of day per work result.
        3. Wage/quantity, cost per work result
        """

        upkeep_labour_ids = self.env['estate.upkeep.labour'].search([('upkeep_id', '=', self.upkeep_id.id),
                                                                     ('activity_id', '=', self.activity_id.id)])

        number_of_day = sum(labour.number_of_day for labour in upkeep_labour_ids)
        quantity_piece_rate = sum(labour.quantity_piece_rate for labour in upkeep_labour_ids)
        activity_standard_base = self.activity_id.qty_base
        quantity = sum(labour.quantity for labour in upkeep_labour_ids)
        amount = sum(labour.amount for labour in upkeep_labour_ids)

        try:
            total_days = number_of_day + (quantity_piece_rate/activity_standard_base)
        except ZeroDivisionError:
            total_days = 0

        try:
            self.ratio_quantity_day = quantity / total_days
        except ZeroDivisionError:
            self.ratio_quantity_day = 0

        try:
            self.ratio_day_quantity = total_days / quantity
        except ZeroDivisionError:
            self.ratio_day_quantity = 0

        try:
            self.ratio_wage_quantity = amount / quantity
        except ZeroDivisionError:
            self.ratio_wage_quantity = 0

    @api.onchange('upkeep_id')
    def _onchange_upkeep(self):
        """Set domain for location while create new record
        """
        if self.upkeep_id.division_id:
            return {
                'domain': {'location_ids': [('inherit_location_id.location_id', '=', self.upkeep_id.division_id.id)]}
            }

class UpkeepLabour(models.Model):
    """
    Maintain work result and its work day(s) equivalent.
    """
    _name = 'estate.upkeep.labour'
    _order = 'employee_id asc'

    name = fields.Char('Name', compute='_compute_name')
    upkeep_id = fields.Many2one('estate.upkeep', string='Upkeep', ondelete='cascade')
    upkeep_date = fields.Date(related='upkeep_id.date', string='Date', store=True)
    upkeep_team_id = fields.Many2one(related='upkeep_id.team_id', string='Team', store=True)
    upkeep_team_employee_id = fields.Many2one(related='upkeep_id.team_id.employee_id', string='Team Leader', store=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True,
                                  domain=[('contract_type', 'in', ['1', '2'])])
    contract_type = fields.Selection(related='employee_id.contract_type', store=False)
    contract_period = fields.Selection(related='employee_id.contract_period', store=False)
    activity_id = fields.Many2one('estate.activity', 'Activity', domain=[('type', '=', 'normal')],
                                  help='Any update will reset Block.',
                                  required=True)
    activity_uom_id = fields.Many2one('product.uom', 'Unit of Measurement', related='activity_id.uom_id')
    activity_standard_base = fields.Float(related='activity_id.qty_base')
    location_id = fields.Many2one('estate.block.template', 'Location')
    estate_id = fields.Many2one(related='upkeep_id.estate_id', store=True)
    division_id = fields.Many2one(related='upkeep_id.division_id', store=True)
    attendance_code_id = fields.Many2one('estate.hr.attendance', 'Attendance',
                                    help='Any update will reset employee\'s timesheet')
    attendance_code_ratio = fields.Float('Ratio', digits=(4,2), related='attendance_code_id.qty_ratio')
    quantity = fields.Float('Quantity', help='Define total work result')
    quantity_piece_rate = fields.Float('Piece Rate', help='Define piece rate work result')
    quantity_overtime = fields.Float('Overtime', help='Define wage based on hour(s)')
    number_of_day = fields.Float('Work Day', help='Maximum 1', compute='_compute_number_of_day', store=True)
    wage_number_of_day = fields.Float('Daily Wage', compute='_compute_wage_number_of_day', store=True)
    wage_overtime = fields.Float('Overtime Wage', compute='_compute_wage_overtime', store=True)
    wage_piece_rate = fields.Float('Piece Rate Wage', compute='_compute_piece_rate', store=True)
    #unit_amount = fields.Float('Unit Amount') # deprecated
    #unit_extra_amount = fields.Float('Unit Extra') # Prestasi Premi
    #extra_amount = fields.Float('Extra Amount') # Premi
    amount = fields.Float('Wage', compute='_compute_amount', store=True, help='Sum of daily, piece rate and overtime wage')
    ratio_quantity_day = fields.Float('Ratio Quantity/Day', compute='_compute_ratio', store=True,
                                      help='Included piece rate conversion to number of day based on activity standard base')
    ratio_day_quantity = fields.Float('Ratio Day/Quantity', compute='_compute_ratio', store=True,
                                      help='Included piece rate conversion to number of day based on activity standard base')
    ratio_wage_quantity = fields.Float('Ratio Wage/Quantity', compute='_compute_ratio', store=True,
                                       help='Included piece rate conversion to number of day based on activity standard base')
    var_quantity_day = fields.Float('Variance Qty/Day (%)', compute='_compute_variance', store=True, digits=(2,0),
                                    help='Reality to standard difference variance')
    prod_quantity_day = fields.Float('Productivity Qty/Day (%)', compute='_compute_prod', store=True, digits=(2, 0),
                                     group_operator="avg", help='Achievement over standard.')

    comment = fields.Text('Remark')
    state = fields.Selection(related='upkeep_id.state')  # todo ganti dg context

    @api.multi
    @api.depends('employee_id')
    def _compute_name(self):
        for record in self:
            record.name = record.employee_id.name

    @api.one
    def _compute_division(self):
        """Define location domain while editing record
        """
        self.division_id = self.upkeep_id.division_id

    @api.one
    @api.depends('attendance_code_ratio', 'activity_standard_base', 'quantity')
    def _compute_number_of_day(self):
        """Define number of days based on attendance code and work result
        Condition:
        1. A day work and work result > activity standard = 1 day.
        2. A day work and work result more than half of standard = 0.5 day.
        3. A half day work and work result more than half of standard = 0.5 day.
        4. Else = 0 day.
        """
        att_ratio = self.attendance_code_ratio
        base = self.activity_standard_base # todo adjust base to estate block parameter
        quantity = self.quantity

        if att_ratio > 0 and quantity >= base:
            result = 1
        elif att_ratio > 0 and base > quantity >= base/2:
            result = 0.5
        else:
            result = 0

        self.number_of_day = result

    @api.one
    @api.depends('number_of_day', 'employee_id', 'upkeep_date', 'estate_id')
    def _compute_wage_number_of_day(self):
        """Daily wage calculated from number of days exclude. Use regional minimum wage if employee
        has no contract.
        """
        # Get default wage
        wage = self.env['estate.wage'].search([('active', '=', True),
                                               ('date_start', '<=', self.upkeep_date),
                                               ('estate_id', '=', self.estate_id.id)],
                                              order='date_start desc',
                                              limit=1)

        # Check contract if any (before upkeep date)
        newest_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id),
                                                          ('date_start', '<=', self.upkeep_date)],
                                                         order='date_start desc',
                                                         limit=1)

        # Contract override regional wage setting
        if newest_contract:
            daily_wage = newest_contract.wage / wage.number_of_days
        else:
            daily_wage = wage.daily_wage

        self.wage_number_of_day = self.number_of_day * daily_wage

    @api.one
    @api.depends('quantity_overtime')
    def _compute_wage_overtime(self):
        """Overtime applied only for PKWTT labour (see view xml)
        """
        if self.quantity_overtime:
            self.wage_overtime = self.quantity_overtime * overtime_amount

    @api.one
    @api.depends('quantity_piece_rate', 'activity_id')
    def _compute_piece_rate(self):
        """"Piece rate applied only for PKWT labour (see view xml)
        """
        if self.quantity_piece_rate:
            # Use standard price if piece rate not set
            if self.activity_id.piece_rate_price:
                result = self.activity_id.piece_rate_price
            else:
                result = self.activity_id.standard_price

            self.wage_piece_rate = self.quantity_piece_rate * result

    @api.one
    @api.depends('wage_number_of_day', 'wage_overtime', 'wage_piece_rate')
    def _compute_amount(self):
        self.amount = self.wage_number_of_day + self.wage_overtime + self.wage_piece_rate

    @api.multi
    @api.depends('ratio_quantity_day', 'ratio_day_quantity', 'ratio_wage_quantity',
                 'attendance_code_id', 'number_of_day', 'quantity', 'quantity_piece_rate', 'amount')
    def _compute_ratio(self):
        """Measure productivity and cost based on quantity or piece rate.
        Precision, required piece rate conversion to day based on activity standard base
        1. Quantity/Day, number of work result per day.
        2. Day/quantity, number of day per work result.
        3. Wage/quantity, cost per work result
        """

        try:
            total_days = self.number_of_day + (self.quantity_piece_rate/self.activity_standard_base)
        except ZeroDivisionError:
            total_days = 0

        try:
            self.ratio_quantity_day = self.quantity / total_days
        except ZeroDivisionError:
            self.ratio_quantity_day = 0

        try:
            self.ratio_day_quantity = total_days / self.quantity
        except ZeroDivisionError:
            self.ratio_day_quantity = 0

        try:
            self.ratio_wage_quantity = self.amount / self.quantity
        except ZeroDivisionError:
            self.ratio_wage_quantity = 0

    @api.one
    @api.depends('quantity', 'activity_standard_base')
    def _compute_variance(self):
        """Quantity to activity standard base variance (productivity)
        """
        #self.ensure_one()
        base = self.activity_standard_base
        if base:
            result = (100 * (self.quantity/base)) - 100
        else:
            result = 0

        self.var_quantity_day = result

    @api.one
    @api.depends('quantity', 'activity_standard_base')
    def _compute_prod(self):
        """Achievement over standard base
        """
        #self.ensure_one()
        base = self.activity_standard_base
        if base:
            result = (self.quantity/base) * 100
        else:
            result = 0

        self.prod_quantity_day = result

    @api.multi
    @api.constrains('quantity_piece_rate')
    def _onchange_piece_rate(self):
        """Piece rate should not exceed variance of daily standard and activity quantity
        """
        self.ensure_one()
        base = self.activity_standard_base
        att_ratio = self.attendance_code_ratio
        quantity = self.quantity
        employee = self.employee_id.name
        activity = self.activity_id.name

        if self.quantity_piece_rate:
            result = quantity - (base * att_ratio)
            if result < 0:
                error_msg = '%s not allowed to have piece rate due to under achievement of %s' % (employee, activity)
                raise exceptions.ValidationError(error_msg)
            elif self.quantity_piece_rate > result:
                error_msg = '%s work at %s piece rate quantity should not exceed %s' % (employee, activity, result)
                raise exceptions.ValidationError(error_msg)

    # @api.one
    # @api.onchange('upkeep_id')
    # def _onchange_upkeep(self):
    #     """
    #     Set domain for location while create new record
    #     """
    #     if self.upkeep_id.division_id:
    #         return {
    #             'domain': {'location_id': [('inherit_location_id.location_id', '=', self.upkeep_id.division_id.id)]}
    #         }

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        """Remove sum.
        """

        # No need to sum quantity and piece rate from different activities.
        if 'quantity' in fields:
            fields.remove('quantity')

        if 'quantity_piece_rate' in fields:
            fields.remove('quantity_piece_rate')

        return super(UpkeepLabour, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby, lazy)

class UpkeepMaterial(models.Model):
    """
    Record material usage by activity. Limit activity domain based on upkeep's activities and locations
    """
    _name = 'estate.upkeep.material'

    name = fields.Char('Name', compute='_compute_name')
    upkeep_id = fields.Many2one('estate.upkeep', 'Upkeep', ondelete='cascade')
    upkeep_date = fields.Date(related='upkeep_id.date', string='Date', store=True)
    activity_id = fields.Many2one('estate.activity', 'Activity',
                                  help='Any update will reset Block.',
                                  required=True)
    activity_uom_id = fields.Many2one('product.uom', 'Unit of Measure', related='activity_id.uom_id',
                                      readonly=True)
    activity_unit_amount = fields.Float('Activity Unit', compute='_compute_activity_unit_amount', help='Based on upkeep activity')
    product_id = fields.Many2one('product.product', 'Material',
                                 domain=[('categ_id.estate_product', '=', True)])
    product_standard_price = fields.Float(related='product_id.standard_price', store=True)
    product_uom_id = fields.Many2one('product.uom', 'Unit of Measure', related='product_id.uom_id',
                                     help="Default Unit of Measure used for all of stock operation",
                                     readonly=True)
    unit_amount = fields.Float('Unit Amount', help="")
    amount = fields.Float('Cost', compute='_compute_amount', store=True)
    ratio_product_activity = fields.Float(compute='_compute_ratio', digits=(18, 6), group_operator="avg", store=True)
    comment = fields.Text('Remark')
    state = fields.Selection(related='upkeep_id.state')  # todo ganti dg context

    @api.multi
    @api.depends('product_id')
    def _compute_name(self):
        for record in self:
            record.name = record.product_id.name

    @api.one
    @api.depends('product_standard_price', 'unit_amount')
    def _compute_amount(self):
        """Get cost from product standard price
        """
        if self.product_standard_price:
            cost = self.product_standard_price
            unit_amount = self.unit_amount
            if cost and unit_amount:
                res = cost * unit_amount
                self.amount = res

    @api.depends('activity_unit_amount', 'unit_amount')
    def _compute_ratio(self):
        activity = self.activity_unit_amount
        product = self.unit_amount
        if activity and product:
            try:
                res = product/activity
            except ZeroDivisionError:
                res = 0
            self.ratio_product_activity = res
            return res
        return False

    @api.onchange('activity_id')
    def _onchange_activity(self):
        activity = self.upkeep_id.get_activity()
        if activity:
            return {
                'domain': {'activity_id': [('complete_name', 'in', activity), ('type', '=', 'normal')]}
            }
        else:
            error_msg = 'Upkeep activity should be defined.'
            raise exceptions.ValidationError(error_msg)

    @api.multi
    @api.depends('upkeep_id', 'activity_id')
    def _compute_activity_unit_amount(self):
        """
        Required to calculate ratio product activity
        """
        for record in self:
            if record.upkeep_id and record.activity_id:
                # Upkeep activity or Labour activity?
                upkeep_activity_id = self.env['estate.upkeep.activity'].search([('upkeep_id', '=', record.upkeep_id.id),
                                                                                ('activity_id', '=', record.activity_id.id)],
                                                                               limit=1)
                record.activity_unit_amount = upkeep_activity_id.unit_amount