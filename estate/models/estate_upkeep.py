# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
import pytz
from openerp.exceptions import ValidationError
from lxml import etree

estate_working_days = 25 # todo create working calendar
overtime_amount = 10000

RESET_PERIOD = [('year', 'Every Year'), ('month', 'Every Month')]
RESET_PERIOD_TIMEDELTA = [('year', 12), ('month', 1)]

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
    _description = 'Upkeep'
    _order = 'date, team_id'
    _inherit = 'mail.thread'

    name = fields.Char("Name", required=True, store=True, default='New')
    assistant_id = fields.Many2one('hr.employee', "Assistant", required=True)  # constrains: if team_id.assistant_id = true
    team_id = fields.Many2one('estate.hr.team', "Team", required=True)
    team_member_ids = fields.One2many(related='team_id.member_ids', string='Member', store=False)
    date = fields.Date("Date", default=fields.Date.context_today, required=True)
    max_day = fields.Integer("Date Constraint", help='Change to override maximum upkeep date day(s) configuration')
    description = fields.Text("Description")
    estate_id = fields.Many2one('stock.location', "Estate",
                                domain=[('estate_location', '=', True), ('estate_location_level', '=', '1'),
                                ('estate_location_type', '=', 'planted')])
    # constrains: limit to estate_id childs
    company_id = fields.Many2one('res.company', 'Company', help='Define location company.')
    division_id = fields.Many2one('stock.location', "Division", required=True,
                                  domain=[('estate_location', '=', True), ('estate_location_level', 'in', ['1','2'])])

    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('approved', 'Approved'),
                              ('correction', 'Correction'),
                              ('payslip', 'Payslip Processed')], "State", default="draft", track_visibility="onchange")
    activity_line_ids = fields.One2many('estate.upkeep.activity', string='Upkeep Activity Line', inverse_name='upkeep_id')
    labour_line_ids = fields.One2many('estate.upkeep.labour', string='Upkeep Labour Line', inverse_name='upkeep_id')
    # constrains: material_ids.product_id = activity_ids.product_id
    material_line_ids = fields.One2many('estate.upkeep.material', string='Upkeep Material Line', inverse_name='upkeep_id')
    comment = fields.Text('Additional Information')

    @api.model
    def create(self, vals):
        """ Get sequence for upkeep """
        if vals.get('name', 'New') == 'New':
            seq_obj = self.env['ir.sequence']
            seq_upkeep = seq_obj.search([('code', '=', 'estate.upkeep')], limit=1)
            delta = [item for item in RESET_PERIOD_TIMEDELTA if item[0] == seq_upkeep.reset_period]
            reset_time_datetime = datetime.strptime(seq_upkeep.reset_time, '%Y-%m-%d %H:%M:%S')

            # Upkeep sequence reset monthly
            previous_reset_time = reset_time_datetime - relativedelta(months=delta[0][1], day=1)
            tx_date = datetime.strptime(vals['date'], '%Y-%m-%d')

            if tx_date < previous_reset_time:
                # Backdate upkeep sequence code cannot use postgres
                period_start = tx_date - relativedelta(day=1)
                period_end = tx_date + relativedelta(months=+1, day=1, days=-1)
                upkeep_ids = self.env['estate.upkeep'].search([('date', '>=', period_start.strftime('%Y-%m-%d')),
                                                               ('date', '<=', period_end.strftime('%Y-%m-%d'))])

                # Return next number or 1
                prefix_length = len(seq_upkeep.get_prefix_char(seq_upkeep.prefix, tx_date))
                if upkeep_ids:
                    seq_codes = []
                    for item in upkeep_ids:
                        try:
                            seq_codes.append(int(item.name[prefix_length:]))
                        except ValueError:
                            # old upkeep name included string
                            seq_codes.append(0)

                    number_next = max(seq_codes) + 1
                else:
                    # No upkeep found
                    number_next = 1

                vals['name'] = seq_upkeep.get_prefix_char(seq_upkeep.prefix, tx_date) \
                               + '%%0%sd' % seq_upkeep.padding % number_next \
                               + seq_upkeep.get_prefix_char(seq_upkeep.suffix, tx_date)
            else:
                vals['name'] = seq_obj.with_context(ir_sequence_date=vals['date']).next_by_code('estate.upkeep') or '/'

        return super(Upkeep, self).create(vals)

    @api.one
    @api.onchange('team_id')
    def _onchange_team_id(self):
        """Automate Assistant and Division selection
        """
        if self.team_id:

            if self.team_id.assistant_id:
                self.assistant_id = self.team_id.assistant_id

            if self.team_id.division_id:
                self.division_id = self.team_id.division_id.id

        return True

    # @api.one
    # @api.onchange('assistant_id')
    # def _onchange_assistant_id(self):
    #     """No need to entry block (division level)
    #     :return: first block and set to division_id
    #     """
    #     if not self.assistant_id:
    #         return
    #
    #     # Limit 1
    #     block = self.env['estate.block.template'].search([('assistant_id', '=', self.assistant_id.id)],
    #                                                      limit=1,
    #                                                      order='id')
    #     block_level = block.estate_location_level
    #
    #     if int(block_level) > 2:
    #         # Block is level 3 or 4
    #         # print '_onchange_assistant_id #2: Block level 3/4 ... cari divisi nya'
    #         res = self.env['stock.location'].get_division(block.inherit_location_id.id)
    #         self.division_id = res.id
    #     elif int(block_level) == 2:
    #         # Block is level 2
    #         self.division_id = block.inherit_location_id.id
    #     else:
    #         # Blok is level 1
    #         return

    @api.one
    @api.onchange('division_id')
    def _onchange_division_id(self):
        """Select estate automatically, update location domain in upkeep line
        :return: first estate and set to estate_id
        """
        if self.division_id and self.division_id.estate_location_level != '1':
            self.estate_id = self.env['stock.location'].get_estate(self.division_id.id)
        elif self.division_id.estate_location_level == '1':  # Costing non block
            self.estate_id = self.division_id.id

    @api.one
    @api.constrains('date')
    def _check_date(self):
        """Upkeep date should be limited. Didn't support different timezone
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

    @api.multi
    @api.constrains('activity_line_ids')
    def _check_activity_line(self):
        """ Upkeep activity should only set once.
        """
        for record in self:
            domains = []
            if not record.activity_line_ids:
                return

            for activity in record.activity_line_ids.mapped('activity_id'):
                domains = ([('upkeep_id', 'in', self.ids), ('activity_id', '=', activity.id)])
                res = record.activity_line_ids.search(domains)

                # Upkeep activity should set once
                if len(res) > 1:
                    error_msg = _("Upkeep Activity %s should only set once" % activity.name)
                    raise ValidationError(error_msg)

                labour_line = self.labour_line_ids.search(domains)
                sum_labour_quantity = sum(line.quantity for line in labour_line)
                unit_amount = res.unit_amount

                # Sum of labour quantity less than or equal to unit amount
                if sum_labour_quantity > unit_amount:
                    error_msg = _("Total %s labour's amount should equal or less than %s" % (activity.name, unit_amount))
                    raise ValidationError(error_msg)

        return True

    @api.multi
    @api.constrains('labour_line_ids')
    def _check_labour_line(self):
        """Check total unit amount of labour equal or less than upkeep unit amount and Total attendance ratio should not exceed 1
        """
        for record in self:
            # End if empty
            if not record.labour_line_ids:
                return

            for activity in record.labour_line_ids.mapped('activity_id'):
                # Check labour activity in upkeep activity
                if not activity in record.activity_line_ids.mapped('activity_id'):
                    error_msg = _('There is no %s in Upkeep Activity list' % activity.name)
                    raise ValidationError(error_msg)

                domains = ([('upkeep_id', 'in', self.ids), ('activity_id', '=', activity.id)])
                sum_quantity = sum(line.quantity for line in record.labour_line_ids.search(domains))
                res = record.activity_line_ids.search(domains)

                # Check sum of labour quantity
                if sum_quantity > res.unit_amount:
                    error_msg = _("Total %s labour's amount should equal or less than %s" % (activity.name, res.unit_amount))
                    raise ValidationError(error_msg)

            # Labour should not worked more than 1 worked day
            for labour in record.labour_line_ids.mapped('employee_id'):
                domains = ([('upkeep_id', 'in', self.ids), ('employee_id', '=', labour.id)])
                sum_attendance_code_ratio = sum(line.attendance_code_ratio for line in record.labour_line_ids.search(domains))
                if sum_attendance_code_ratio > 1:
                    error_msg = _("Total worked day of %s should not more than 1 worked day" % labour.name)
                    raise ValidationError(error_msg)

    @api.multi
    @api.constrains('material_line_ids')
    def _check_material_line(self):
        """Check activity of material usage
        """
        for record in self:
            # End if empty
            if not record.material_line_ids:
                return

            for activity in record.material_line_ids.mapped('activity_id'):
                # Check material usage activity in upkeep activity
                if not activity in record.activity_line_ids.mapped('activity_id'):
                    error_msg = _('There is no %s in Upkeep Activity list' % activity.name)
                    raise ValidationError(error_msg)

    @api.multi
    def get_activity(self):
        """Labour's activity should match with upkeep activity
        :return: list of string (activity complete name)
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
    def get_activity_location(self, activity_id):
        """
        Upkeep labour location required to match with upkeep activity
        :param activity_id:
        :return: list of location object
        """
        location_ids = []
        for record in self:
            if record.activity_line_ids:
                for activity in record.activity_line_ids:
                    location_ids.append(activity.location_ids)
                return location_ids

    @api.multi
    def get_labour(self, activity):
        labour = []
        records = self.labour_line_ids
        for record in records.search([('activity_id', '=', activity)]):
            labour.append(record.employee_id.name)
        if len(labour):
            return labour
        return False

    # Deprecated
    # @api.multi
    # def get_labour_activity(self):
    #     """Return set of labour's activity
    #     :return: list of activity or False
    #     """
    #     labour_line_activity = []
    #     for activity in self.labour_line_ids:
    #         labour_line_activity.append(activity.activity_id.id)
    #     if len(labour_line_activity):
    #         return set(labour_line_activity)
    #     return False

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
        labour_activity = self.labour_line_ids.mapped('activity_id')

        # Calculate quantity per labour
        for activity_id in labour_activity:
            # qty_ratio = activity_qty/((att_ratio_1.lbr1)+(att_ratio_2.lbr2)+(att_ratio_x.lbrx))

            activity_qty = self.activity_line_ids.search([('activity_id', '=', activity_id.id),
                                                          ('upkeep_id', 'in', self.ids)], limit=1).unit_amount

            # get unique attendance code
            labour_attendance = self.get_labour_attendance(activity_id.id)

            if labour_attendance:
                attendance_amount_ratio = []
                for attendance_id in labour_attendance:
                    # get attendance code ratio
                    att_ratio = self.env['estate.hr.attendance'].search([('id', '=', attendance_id)], limit=1).qty_ratio
                    # count labour
                    filter_labour = [('activity_id', '=', activity_id.id),
                                     ('attendance_code_id', '=', attendance_id),
                                     ('upkeep_id', 'in', self.ids)]
                    labour_amount = len(self.labour_line_ids.search(filter_labour))
                    # calculate attendance amount ratio per attendance code
                    attendance_amount_ratio.append(att_ratio * labour_amount)

                # calculate quantity ratio
                qty_ratio = activity_qty / sum(attendance_amount_ratio)
                # Update labour quantity
                self.set_labour_qty(qty_ratio, activity_id.id)

        return True

    @api.one
    def button_confirmed(self):
        # Nothing to be confirmed.
        if not self.labour_line_ids and self.state == 'draft':
            error_msg = _("No Upkeep Labour need to be confirmed")
            raise ValidationError(error_msg)

        self.write({
            'state': 'confirmed'
        })

    @api.one
    def button_approved(self):
        # Nothing to be approved.
        if not self.labour_line_ids and self.state == 'draft':
            error_msg = _("No Upkeep Labour need to be confirmed")
            raise ValidationError(error_msg)

        # todo create analytic journal entry here

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


    @api.multi
    def reset_all_quantity(self, activity):
        """
        Upkeep activity onchange required to reset all quantity, overtime and piecerate
        :return:
        """
        # for record in self.labour_line_ids:
        #     record.write({'quantity':0, 'quantity_overtime': 0, 'quantity_piece_rate': 0})

        # for labour in self.labour_line_ids.search([('activity_id', '=', activity.id)]):
        for labour in self.labour_line_ids:
            val = {
                'quantity': 0,
                'quantity_overtime': 0,
                'quantity_piece_rate': 0,
                'number_of_day': 0,
                'attendance_code_id': False,
            }
            labour.write(val)

        # for activity in self.activity_line_ids.search([('activity_id', '=', activity.id)]):
        for activity in self.activity_line_ids:
            val = {
                'amount': 0,
            }
            activity.write(val)


class UpkeepActivity(models.Model):
    """
    Required for calculate quantity and constraints. Future use as Daily Plan.
    """
    _name = 'estate.upkeep.activity'
    _description = 'Upkeep Activity'
    _inherit = 'mail.thread'
    # _inherits = {'account.analytic.line': 'line_id'}

    name = fields.Char('Name', compute='_compute_name')
    upkeep_id = fields.Many2one('estate.upkeep', string='Upkeep', ondelete='cascade')
    upkeep_date = fields.Date(related='upkeep_id.date', store=True)
    # line_id = fields.Many2one('account.analytic.line', 'Analytic Line', ondelete='cascade', required=True),
    activity_id = fields.Many2one('estate.activity', 'Activity', domain=[('type', '=', 'normal'),('activity_type', '=', 'estate')],
                                  track_visibility='onchange', help='Any update will reset Block.', required=True)
    activity_uom_id = fields.Many2one('product.uom', 'Unit of Measurement', related='activity_id.uom_id')

    location_ids = fields.Many2many('estate.block.template', id1='activity_id', id2='location_id', string='Location',
                                    track_visibility='onchange')
    division_id = fields.Many2one('stock.location', compute='_compute_division')
    unit_amount = fields.Float('Quantity', digits=dp.get_precision('Estate'), track_visibility='onchange',
                               help="Required to distribute work result of labour "\
                                    "based on activity and attendance ratio.") # constrains sum of labour activity quantity
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
    account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                 domain="[('use_estate', '=', True), ('account_type', '=', 'normal')]",
                                 help='Select analytic account for costing by seed batch or planted year')
    comment = fields.Text('Remark')
    state = fields.Selection(related='upkeep_id.state', store=True)  # todo ganti dg context
    ratio_quantity_day = fields.Float('Ratio Quantity/Day', compute='_compute_ratio', store=True, group_operator="avg",
                                      digits=dp.get_precision('Estate'),
                                      help='Work result within a work day.')
    ratio_day_quantity = fields.Float('Ratio Day/Quantity', compute='_compute_ratio', store=True, group_operator="avg",
                                      digits=dp.get_precision('Estate'),
                                      help='Amount of day required to finish a work.')
    ratio_wage_quantity = fields.Float('Ratio Wage/Quantity', compute='_compute_ratio', store=True, group_operator="avg",
                                       digits=dp.get_precision('Account'),
                                       help='Amount of wage paid to finish a work')
    activity_contract = fields.Boolean('Activity Contract', related='activity_id.contract', readonly=True)  # Different ACL
    # contract = fields.Boolean('Activity Contract', default=False, help='Use only for contract based upkeep activity')
    cross_team = fields.Boolean('Cross Team Activity', help='Check to open all locations.')

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
            self.labour_amount = upkeep_labour_sum

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
        for record in self:
            upkeep_labour_ids = self.env['estate.upkeep.labour'].search([('upkeep_id', '=', record.upkeep_id.id),
                                                                         ('activity_id', '=', record.activity_id.id)])

            number_of_day = sum(labour.number_of_day for labour in upkeep_labour_ids)
            quantity_piece_rate = sum(labour.quantity_piece_rate for labour in upkeep_labour_ids)
            activity_standard_base = record.activity_id.qty_base
            quantity = sum(labour.quantity for labour in upkeep_labour_ids)
            amount = sum(labour.amount for labour in upkeep_labour_ids)

            try:
                total_days = number_of_day + (quantity_piece_rate/activity_standard_base)
            except ZeroDivisionError:
                total_days = 0

            try:
                record.ratio_quantity_day = quantity / total_days
            except ZeroDivisionError:
                record.ratio_quantity_day = 0

            try:
                record.ratio_day_quantity = total_days / quantity
            except ZeroDivisionError:
                record.ratio_day_quantity = 0

            try:
                record.ratio_wage_quantity = amount / quantity
            except ZeroDivisionError:
                record.ratio_wage_quantity = 0

    @api.onchange('upkeep_id')
    def _onchange_upkeep(self):
        """Set domain for location while create new record
        """
        print '_onchange_upkeep activity'
        if not self.upkeep_id:
            warning = {
                    'title': _('Warning!'),
                    'message': _('Material Usage should be created within Daily Upkeep'),
                }
            return {'warning': warning}

        if self.upkeep_id.division_id:
            # non block domain
            return {
                'domain': {'location_ids': [('inherit_location_id.location_id', 'in', (self.upkeep_id.estate_id.id,
                                                                                       self.upkeep_id.division_id.id)),
                                            ('company_id', '=', self.upkeep_id.company_id.id),
                                            ('estate_location_level', '=', '3')]}
            }

    @api.onchange('location_ids')
    def _onchange_location_ids(self):
        """Division should be defined first
        """
        if not self.upkeep_id:
            return

        division = self.upkeep_id.division_id

        if not division:
            warning = {
                    'title': _('Warning!'),
                    'message': _('You must first select a Division!'),
                }
            return {'warning': warning}

    @api.onchange('cross_team')
    def _onchange_cross_team(self):
        if self.cross_team:
            return {
                'domain': {'location_ids': [('estate_location_level', '=', '3')]}
            }
        else:
            # Put back domain
            return {
                'domain': {'location_ids': [('inherit_location_id.location_id', 'in', (self.upkeep_id.estate_id.id,
                                                                                       self.upkeep_id.division_id.id)),
                                            ('company_id', '=', self.upkeep_id.company_id.id),
                                            ('estate_location_level', '=', '3')]}
            }


class UpkeepLabour(models.Model):
    """
    Maintain work result and its work day(s) equivalent.
    """
    _name = 'estate.upkeep.labour'
    _description = 'Upkeep Labour'
    _inherit = 'mail.thread'
    _order = 'activity_id asc, employee_id asc'

    # @api.multi
    # def default_activity_location_ids(self):
    #     """ Fill in surrogate field for upkeep labour location domain """
        # for record in self:
        #     upkeep_activity_id = record.upkeep_id.activity_line_ids.search([('activity_id', '=', record.activity_id.id)])
        #     print 'upkeep activity %s' % upkeep_activity_id
        #     if not upkeep_activity_id:
        #         return
        #     else:
        #         record.activity_location_ids = upkeep_activity_id.mapped('location_ids').ids

    name = fields.Char('Name', compute='_compute_name')
    upkeep_id = fields.Many2one('estate.upkeep', string='Upkeep', ondelete='cascade')
    upkeep_date = fields.Date(related='upkeep_id.date', string='Date', store=True)
    upkeep_team_id = fields.Many2one(related='upkeep_id.team_id', string='Team', store=True)
    upkeep_team_employee_id = fields.Many2one(related='upkeep_id.team_id.employee_id', string='Team Leader', store=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, track_visibility='onchange',
                                  domain=[('contract_type', 'in', ['1', '2'])])
    employee_company_id = fields.Many2one(related='employee_id.company_id', string='Employee Company', store=True,
                                          help="Company of employee")
    contract_type = fields.Selection(related='employee_id.contract_type', store=False)
    contract_period = fields.Selection(related='employee_id.contract_period', store=False)
    nik_number = fields.Char(related='employee_id.nik_number', store=False)
    activity_id = fields.Many2one('estate.activity', 'Activity', domain=[('type', '=', 'normal'),('activity_type', '=', 'estate')],
                                  help='Any update will reset Block.', required=True)
    activity_uom_id = fields.Many2one('product.uom', 'Unit of Measurement', related='activity_id.uom_id')
    activity_wage_method = fields.Selection('Wage Method', related='activity_id.wage_method', readonly=True)
    activity_standard_base = fields.Float(related='activity_id.qty_base')
    general_account_id = fields.Many2one(related='activity_id.general_account_id', store="True")
    location_id = fields.Many2one('estate.block.template', 'Location',
                                  domain="[('inherit_location_id.location_id', '=', division_id)]")
    planted_year_id = fields.Many2one(related='location_id.planted_year_id')
    activity_location_ids = fields.Many2one('estate.block.template', 'Activity Location', store=False,
                                            compute="_compute_activity_location_ids")
    company_id = fields.Many2one(related='location_id.company_id', store=True, help='Company of location')
    estate_id = fields.Many2one(related='upkeep_id.estate_id', store=True)
    division_id = fields.Many2one(related='upkeep_id.division_id', store=True)
    attendance_code_id = fields.Many2one('estate.hr.attendance', 'Attendance', track_visibility='onchange',
                                    help='Any update will reset employee\'s timesheet')
    attendance_code_ratio = fields.Float('Ratio', digits=(4,2), related='attendance_code_id.qty_ratio')
    quantity = fields.Float('Quantity', track_visibility='onchange',
                            help='Define total work result', digits=dp.get_precision('Estate'))
    quantity_piece_rate = fields.Float('Piece Rate', track_visibility='onchange',
                                       help='Define piece rate work result.', digits=dp.get_precision('Estate'))
    quantity_overtime = fields.Float('Overtime', track_visibility='onchange',
                                     help='Define wage based on hour(s)', digits=dp.get_precision('Estate'))
    number_of_day = fields.Float('Work Day', help='Maximum 1', compute='_compute_number_of_day', store=True)
    wage_number_of_day = fields.Float('Daily/Target Wage', compute='_compute_wage_number_of_day', store=True)
    wage_overtime = fields.Float('Overtime Wage', compute='_compute_wage_overtime', store=True)
    wage_piece_rate = fields.Float('Piece Rate Wage', compute='_compute_wage_piece_rate', store=True)
    amount = fields.Float('Wage', compute='_compute_amount', store=True, help='Sum of daily, piece rate and overtime wage')

    ratio_quantity_day = fields.Float('Ratio Quantity/Day', compute='_compute_ratio', store=True, group_operator="avg",
                                      digits=dp.get_precision('Estate'),
                                      help='Work result within a work day.')
    ratio_day_quantity = fields.Float('Ratio Day/Quantity', compute='_compute_ratio', store=True, group_operator="avg",
                                      digits=dp.get_precision('Estate'),
                                      help='Amount of day required to finish a work.')
    ratio_wage_quantity = fields.Float('Ratio Wage/Quantity', compute='_compute_ratio', store=True, group_operator="avg",
                                       digits=dp.get_precision('Account'),
                                       help='Amount of wage paid to finish a work')
    var_quantity_day = fields.Float('Variance Qty/Day (%)', compute='_compute_variance', store=True, digits=(2,0),
                                    group_operator="avg", help='Reality to standard difference variance')
    prod_quantity_day = fields.Float('Productivity Qty/Day (%)', compute='_compute_prod', store=True, digits=(2, 0),
                                     group_operator="avg", help='Achievement over standard in percentage.')
    var_qty_base = fields.Float('Variance to Standard', compute='_compute_var_qty_base', store=True,
                                group_operator="avg", digits=dp.get_precision('Estate'),
                                help='Achievement over standar in quantity.')
    comment = fields.Text('Remark')
    state = fields.Selection(related='upkeep_id.state', store=True)  # todo ganti dg context
    activity_contract = fields.Boolean('Upkeep Activity Contract', compute='_compute_activity_contract',
                                       store=True, readonly=True)
    cross_team_id = fields.Many2one('estate.hr.team', 'Cross Team', help='Set to define cross team upkeep labour.')
    number_of_day_team_id = fields.Many2one('estate.hr.team', 'Upkeep Cross Team', compute='_compute_number_of_day_team_id',
                                            store=True)

    @api.multi
    @api.depends('employee_id')
    def _compute_name(self):
        # domain = {}
        for record in self:
            record.name = record.employee_id.name

    @api.one
    def _compute_division(self):
        """Define location domain while editing record
        """
        self.division_id = self.upkeep_id.division_id

    @api.multi
    @api.depends('attendance_code_id')
    def _compute_activity_contract(self):
        """Required to domain quantity and piece rate"""
        for record in self:
            if record.attendance_code_id.contract:
                record.activity_contract = True
                return

    @api.one
    @api.depends('attendance_code_ratio', 'activity_standard_base', 'quantity')
    def _compute_number_of_day(self):
        """Define number of days based on attendance code and work result

        Standard based condition
        1. A day/half day work and work result > activity standard = 1 day.
        2. A day work and work result more than half of standard = 0.5 day.
        3. A half day work and work result more than half of standard = 0.5 day.
        4. Else = 1 * attendance ratio day.
        5. If contract based return 0

        Attendance based condition
        1. Return attendance code ratio
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

        if self.activity_id.wage_method == 'standard':
            if not self.activity_contract:
                self.number_of_day = result
            else:
                # Number of day for target based activity created confusion.
                self.number_of_day = 0
        elif self.activity_id.wage_method == 'attendance':
            self.number_of_day = att_ratio

    @api.one
    @api.depends('number_of_day', 'employee_id', 'upkeep_date', 'estate_id', 'quantity')
    def _compute_wage_number_of_day(self):
        """Daily/quantity wage calculated from number of days exclude. Use regional minimum wage if employee
        has no contract.
        """

        # Prevent computing when no activity line defined.
        if not self.upkeep_id.activity_line_ids:
            error_msg = _('Upkeep Activity should be defined first')
            raise ValidationError(error_msg)

        # Latest estate's regional wage (upkeep date and not expired)
        wage = self.env['estate.wage'].search([('active', '=', True),
                                               ('date_start', '<=', self.upkeep_date),
                                               ('estate_id', '=', self.estate_id.id),
                                               ('active', '=', True)],
                                              order='date_start desc',
                                              limit=1)
        if not wage:
            if not self.upkeep_id.activity_line_ids:
                # For empty activity line
                error_msg = _('Upkeep Activity should be defined first')
            else:
                error_msg = _("No Regional Wage defined.")
            raise ValidationError(error_msg)

        # Latest contract before upkeep date if any
        newest_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id),
                                                          ('date_start', '<=', self.upkeep_date)],
                                                         order='date_start desc',
                                                         limit=1)

        # Contract override regional wage
        if newest_contract:
            try:
                daily_wage = newest_contract.wage / wage.number_of_days
            except ZeroDivisionError:
                daily_wage = 0
        else:
            daily_wage = wage.daily_wage

        # Use wage_number_of_day to save cost from number of day based or target based activity.
        if self.attendance_code_id:
            self.wage_number_of_day = self.number_of_day * daily_wage
            # attendance code with contract based
            if self.attendance_code_id.contract and self.employee_id.contract_type == '2' and self.employee_id.contract_period == '2':
                self.wage_number_of_day = self.quantity * self.activity_id.standard_price
        elif self.activity_contract and self.employee_id.contract_type == '2' and self.employee_id.contract_period == '2':
            self.wage_number_of_day = self.quantity * self.activity_id.standard_price


    @api.one
    @api.depends('quantity_overtime')
    def _compute_wage_overtime(self):
        """Overtime applied only for PKWTT labour (see view xml)
        """
        # Get overtime
        estate_overtime = self.env['estate.wage'].get_current_overtime(self.estate_id)
        if estate_overtime:
            self.wage_overtime = estate_overtime * self.quantity_overtime

    @api.one
    @api.depends('quantity_piece_rate', 'activity_id', 'quantity', 'location_id', 'attendance_code_id')
    def _compute_wage_piece_rate(self):
        """"Piece rate applied only for PKWT labour (see view xml)
        """
        # Piece rate wage based on piece rate price unless it not defined.
        unit_price = 0.00
        if self.activity_id.piece_rate_price:
            unit_price = self.activity_id.piece_rate_price
        else:
            unit_price = self.activity_id.standard_price

        # Piece rate as bonus after standard quantity achieved
        if self.quantity_piece_rate and self.quantity > self.activity_id.qty_base:
            self.wage_piece_rate = self.quantity_piece_rate * unit_price

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
        for record in self:
            try:
                total_days = record.number_of_day + (record.quantity_piece_rate/record.activity_standard_base)
            except ZeroDivisionError:
                total_days = 0

            try:
                record.ratio_quantity_day = record.quantity / total_days
            except ZeroDivisionError:
                record.ratio_quantity_day = 0

            try:
                record.ratio_day_quantity = total_days / record.quantity
            except ZeroDivisionError:
                record.ratio_day_quantity = 0

            try:
                record.ratio_wage_quantity = record.amount / record.quantity
            except ZeroDivisionError:
                record.ratio_wage_quantity = 0

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
        """Achievement over standard base in percentage.
        """
        #self.ensure_one()
        base = self.activity_standard_base
        if base:
            result = (self.quantity/base) * 100
        else:
            result = 0

        self.prod_quantity_day = result

    @api.multi
    @api.depends('activity_id', 'quantity')
    def _compute_var_qty_base(self):
        """Achievement over standard in quantity.
        """
        for record in self:
            # Calculate based on activity and quantity
            if record.activity_id:
                record.var_qty_base = record.quantity - record.activity_id.qty_base

    # @api.multi
    # @api.depends('activity_id')
    # def _compute_activity_contract(self):
    #     """ Differentiate Target vs Daily Target """
    #     for record in self:
    #         if not record.upkeep_id:
    #             return
    #         res = record.upkeep_id.activity_line_ids.search([('activity_id', '=', record.activity_id.id)], limit=1)
    #         record.activity_contract = res.contract

    @api.multi
    @api.depends('activity_id')
    def _compute_number_of_day_team_id(self):
        """ Upkeep report by team and cross_team"""
        for record in self:
            if record.cross_team_id:
                record.number_of_day_team_id = record.cross_team_id.id
            else:
                record.number_of_day_team_id = record.upkeep_team_id.id

    @api.multi
    @api.depends('activity_id')
    def _compute_activity_location_ids(self):
        """ Define location based on activity while editing record - not finished """

        # for record in self:
        #     location_ids = record.upkeep_id.activity_line_ids.search([('activity_id', '=', record.activity_id.id)])
        #     record.activity_location_ids = location_ids.mapped('location_ids').ids

    @api.multi
    @api.onchange('upkeep_id')
    def _onchange_upkeep(self):
        """Labour should be created within Daily Upkeep and has upkeep activity set
        """
        if not self.upkeep_id:
            warning = {
                    'title': _('Warning!'),
                    'message': _('Labour Usage should be created within Daily Upkeep'),
                }
            return {'warning': warning}

        if not self.upkeep_id.activity_line_ids:
            warning = {
                'title': _('Warning!'),
                'message': _('Upkeep Activity should be defined first'),
            }
            return {'warning': warning}

        # Filter employee - create only
        # todo domain did'nt work while edit
        for record in self:
            employee_ids = record.upkeep_id.team_id.member_ids.mapped('employee_id')
            return {
                'domain': {
                    'employee_id': [('contract_type', 'in', ['1', '2']),
                                    ('id', 'in', employee_ids.ids)]
                }
            }

    @api.multi
    @api.onchange('activity_id')
    def _onchange_activity_id(self):
        """
        Certain activity has wage method based on attendance code. Required to refresh attendance code when
        activity change
        Upkeep activity has locations. Required to refresh locations domain when activity change.
        :return:
        """
        for record in self:
            # if not record.activity_id:
            #     return

            # Reset attendance code
            record.attendance_code_id = False

            # Domain activity and location
            activity_ids = record.upkeep_id.activity_line_ids.mapped('activity_id')
            # todo domain didn't work at edit
            location_ids = []
            for activity in record.upkeep_id.activity_line_ids:
                if record.activity_id.id == activity.activity_id.id:
                    location_ids = activity.location_ids.ids

            if activity_ids or location_ids:
                if activity_ids:
                    attendance_code_domain = []
                    if record.activity_id.contract:
                        attendance_code_domain = [('contract', 'in', (True, False))]
                    else:
                        attendance_code_domain = [('contract', '=', False)]
                    return {
                        'domain': {
                            'activity_id': [('id', 'in', activity_ids.ids)],
                            'location_id': [('id', 'in', location_ids)],
                            'attendance_code_id': attendance_code_domain,
                        }
                    }
                else:
                    error_msg = _("Upkeep Activity should be defined first")
                    raise ValidationError(error_msg)

    @api.onchange('location_id')
    def _onchange_location_id(self):
        """Division should be defined first
        """
        if not self.upkeep_id:
            return

        division = self.upkeep_id.division_id

        if not division:
            warning = {
                'title': _('Warning!'),
                'message': _('You must first select a Division!'),
                }
            return {'warning': warning}

    @api.multi
    @api.constrains('quantity_piece_rate')
    def _onchange_piece_rate(self):
        """Piece rate should be:
        1. Not excedd variance of daily standard and activity quantity.
        2. Used to calculate PKWT Daily Target achievement (condition: no attendance, unclosed block)
        """
        self.ensure_one()

        base = self.activity_standard_base
        att_ratio = self.attendance_code_ratio
        quantity = self.quantity
        employee = self.employee_id.name
        activity = self.activity_id.name

        if self.quantity_piece_rate:
            # Validate labour quantity and piece rate to standard activity
            result = quantity - (base * att_ratio)
            if result < 0:
                error_msg = _("%s not allowed to have piece rate due to under achievement of %s" % (employee, activity))
                raise ValidationError(error_msg)
            elif self.quantity_piece_rate > result:
                error_msg = _("%s work at %s piece rate quantity should not exceed %s" % (employee, activity, result))
                raise ValidationError(error_msg)

    @api.constrains('attendance_code_id')
    def _check_attendance_code(self):
        """ Attendance code ratio should follow work result number of day calculation """
        if self.attendance_code_id.qty_ratio < self.number_of_day:
            error_msg = _(
                "%s has %s number of day. Please change attendance code." % (self.employee_id.name, self.number_of_day))
            raise ValidationError(error_msg)

        # a labour should not have more than 1 work day in a single day
        upkeep_ids = self.env['estate.upkeep.labour'].search([('employee_id', '=', self.employee_id.id),
                                                              ('upkeep_date', '=', self.upkeep_date)])
        number_of_day = sum(item.number_of_day for item in upkeep_ids)
        if number_of_day > 1:
            error_msg = _(
                "%s has been work for more than 1 worked day." % self.employee_id.name)
            raise ValidationError(error_msg)


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
    _description = 'Upkeep Material'
    _inherit = 'mail.thread'

    name = fields.Char('Name', compute='_compute_name')
    upkeep_id = fields.Many2one('estate.upkeep', string='Upkeep', ondelete='cascade')
    upkeep_date = fields.Date(related='upkeep_id.date', string='Date', store=True)
    activity_id = fields.Many2one('estate.activity', 'Activity', domain=[('type', '=', 'normal'), ('activity_type', '=', 'estate')],
                                  help='Any update will reset Block.', track_visibility = 'onchange', required=True)
    location_id = fields.Many2one('estate.block.template', 'Location',
                                  domain="[('inherit_location_id.location_id', '=', division_id)]")
    activity_uom_id = fields.Many2one('product.uom', 'Unit of Measure', related='activity_id.uom_id',
                                      readonly=True)
    activity_unit_amount = fields.Float('Quantity', compute='_compute_activity_unit_amount',
                                        help='Sum of labour activity quantity.')
    product_id = fields.Many2one('product.product', 'Material', track_visibility='onchange',
                                 domain=[('categ_id.estate_product', '=', True)])
    product_standard_price = fields.Float(related='product_id.standard_price', store=True)
    product_uom_id = fields.Many2one('product.uom', 'Unit of Measure', related='product_id.uom_id',
                                     help="Default Unit of Measure used for all of stock operation",
                                     readonly=True)
    unit_amount = fields.Float('Unit Amount', track_visibility='onchange', help="")
    amount = fields.Float('Cost', compute='_compute_amount', store=True)
    ratio_product_activity = fields.Float('Ratio Product/Activity', compute='_compute_ratio',
                                          help='Amount of product required per activity.',
                                          digits=dp.get_precision('Estate'), group_operator="avg", store=True)
    prod_product_activity = fields.Float('Productivity Material', digits=dp.get_precision('Estate'),
                                         help='Only first option used as reference',
                                         compute='_compute_prod_product_activity', group_operator="avg", store=True)
    comment = fields.Text('Remark')
    state = fields.Selection(related='upkeep_id.state', store=True)  # todo ganti dg context
    company_id = fields.Many2one(related='location_id.company_id', store=True, help='Company of location')
    estate_id = fields.Many2one(related='upkeep_id.estate_id', store=True)
    division_id = fields.Many2one(related='upkeep_id.division_id', store=True)

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

    @api.multi
    @api.depends('activity_unit_amount', 'unit_amount')
    def _compute_ratio(self):
        for record in self:
            activity = record.activity_unit_amount
            product = record.unit_amount
            if activity and product:
                try:
                    res = product/activity
                except ZeroDivisionError:
                    res = 0
                record.ratio_product_activity = res
                return res
            return False

    @api.multi
    @api.depends('activity_id', 'product_id',)
    def _compute_prod_product_activity(self):
        material_obj = self.env['estate.material.norm']
        for record in self:
            if record.activity_id and record.product_id:
                # Only return first option
                material_id = material_obj.search([('activity_id', '=', record.activity_id.id),
                                                   ('product_id', '=', record.product_id.id),
                                                   ('option', '=', 1)])
                res = material_id.unit_amount
                record.prod_product_activity = res
                return res

    @api.multi
    @api.depends('upkeep_id', 'activity_id', 'unit_amount')
    def _compute_activity_unit_amount(self):
        """
        Required to calculate ratio product activity
        """
        for record in self:
            if record.upkeep_id and record.activity_id:
                # Upkeep activity or Labour activity?
                # upkeep_activity_id = self.env['estate.upkeep.activity'].search([('upkeep_id', '=', record.upkeep_id.id),
                #                                                                 ('activity_id', '=', record.activity_id.id)],
                #                                                                limit=1)
                # record.activity_unit_amount = upkeep_activity_id.unit_amount

                # Labour Activity
                labour_activity_ids = self.env['estate.upkeep.labour'].search([('upkeep_id', '=', record.upkeep_id.id),
                                                                               ('activity_id', '=', record.activity_id.id)])
                record.activity_unit_amount = sum(activity.quantity for activity in labour_activity_ids)

    @api.multi
    @api.onchange('upkeep_id')
    def _onchange_upkeep(self):
        """Material should be created within Daily Upkeep
        """
        if not self.upkeep_id:
            warning = {
                    'title': _('Warning!'),
                    'message': _('Material Usage should be created within Daily Upkeep'),
                }
            return {'warning': warning}

        if not self.upkeep_id.activity_line_ids:
            warning = {
                'title': _('Warning!'),
                'message': _('Upkeep Activity should be defined first'),
            }
            return {'warning': warning}

        # if self.upkeep_id.division_id:
        #     return {
        #         'domain': {'location_id': [('inherit_location_id.location_id', '=', self.upkeep_id.division_id.id)]}
        #     }

    @api.multi
    @api.onchange('activity_id')
    def _onchange_activity(self):
        for record in self:
            activity_ids = record.upkeep_id.activity_line_ids.mapped('activity_id')

            # todo domain didn't work at edit
            location_ids = []
            for activity in record.upkeep_id.activity_line_ids:
                if record.activity_id.id == activity.activity_id.id:
                    location_ids = activity.location_ids.ids

            if activity_ids or location_ids:
                if activity_ids:
                    return {
                        'domain': {
                            'activity_id': [('id', 'in', activity_ids.ids)],
                            'location_id': [('id', 'in', location_ids)]
                        }
                    }
                else:
                    error_msg = _("Upkeep Activity should be defined first")
                    raise ValidationError(error_msg)
