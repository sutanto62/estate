# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
from openerp.tools.translate import _
from openerp.exceptions import ValidationError, UserError

class Payslip(models.Model):
    """
    Prepare payslip's worked day and input lines.
    """
    _inherit = 'hr.payslip'

    team_id = fields.Many2one('estate.hr.team', 'Team', compute='_get_team', store=True, help="Employee's original Team")
    division_id = fields.Many2one('stock.location', 'Division', related='team_id.division_id', store=True,
                                  help="Team's Division")
    payroll_location_id = fields.Many2one(related='team_id.payroll_location_id',
                                          store=True, readonly=True)
    contract_type_id = fields.Many2one(related='contract_id.type_id', readonly=True)
    upkeep_labour_count = fields.Integer(compute='_compute_upkeep_labour', string='Payslip Upkeep Labour Details')
    active = fields.Boolean('Active', default=True)

    @api.multi
    @api.depends('employee_id')
    def _get_team(self):
        """Estate worker's payslip disbursed per team after estate assistant confirmed
        """
        for payslip in self:
            upkeep_labour_ids = self.env['estate.upkeep.labour'].search([('employee_id', '=', payslip.employee_id.id),
                                                                         ('upkeep_date', '>=', payslip.date_from),
                                                                         ('upkeep_date', '<=', payslip.date_to),
                                                                         ('state', 'in', ['confirmed', 'approved', 'payslip'])])

            team_ids = []
            for upkeep_labour in upkeep_labour_ids:
                team_ids.append(upkeep_labour.upkeep_id.team_id.id)
            team_ids = list(set(team_ids))


            # Avoid error when KHL registered more than 1 team.
            if team_ids and payslip.contract_type_id.name == 'Estate Worker': # Other employee need no team_id
                payslip.team_id = team_ids[0]
            return True

    @api.multi
    def _get_upkeep_labour(self):
        """
        Get upkeep approved/payslip labour with fingerprint or contract labour after estate assistant confirmed
        Returns: list of ids
        """
        labour_ids = []
        upkeep_labour_ids = self.env['estate.upkeep.labour'].search([('employee_id', '=', self.employee_id.id),
                                                                     ('upkeep_date', '>=', self.date_from),
                                                                     ('upkeep_date', '<=', self.date_to),
                                                                     ('state', 'in', ['confirmed', 'approved', 'payslip'])])
        for item in upkeep_labour_ids:
            # Fingerprint checked at get_inputs and get_worked_day_lines?
            # if item['is_fingerprint'] == 'Yes':
            labour_ids.append(item['id'])

        return labour_ids

    @api.multi
    def _compute_upkeep_labour(self):
        """ Display number of upkeep did by the labour in payslip """
        self.upkeep_labour_count = len(self._get_upkeep_labour())

    @api.multi
    def _check_payslip_team(self):
        """ Check if employee_id registered as a team."""
        # repeat per row
        self.ensure_one()
        start = self.date_from
        end = self.date_to
        employee = self.employee_id.id

        query = 'select ' \
                'a.id, ' \
                'a."number" as kode,' \
                ' d.name_related as khl, ' \
                'c.total_payslip as upah, ' \
                'g.total_bkm as bkm, (g.total_bkm-c.total_payslip) as selisih, ' \
                'a.team_id ' \
                'from hr_payslip a ' \
                'left join (' \
                'select distinct b.slip_id, b.employee_id, sum(b.total) as total_payslip ' \
                'from hr_payslip_line b ' \
                'where b.code in (\'EDW\',\'PR\',\'PRWD\',\'OT\') ' \
                'group by b.slip_id, b.employee_id) as c on c.slip_id = a.id ' \
                'left join hr_employee d on d.id = a.employee_id ' \
                'left join (' \
                'select f.employee_id, sum(f.amount) as total_bkm ' \
                'from estate_upkeep_labour f ' \
                'where ' \
                'f.upkeep_date between \'%s\' ' \
                'and \'%s\' and f.state = \'approved\' ' \
                'group by f.employee_id) as g on g.employee_id = a.employee_id ' \
                'where ' \
                'a.date_from >= \'%s\' ' \
                'and a.date_to <= \'%s\' ' \
                'and a.team_id is null ' \
                'and a.employee_id = \'%s\'' \
                'order by d.name_related asc' % (start, end, start, end, employee)
        self._cr.execute(query)
        res = self._cr.dictfetchall()
        # change list of single dict to dict
        return {k:v for x in res for k,v in x.items()}

    @api.multi
    def _check_payslip_wage(self):
        """ Display difference between upkeep labour and payslip. Recompute will eliminate difference."""
        for record in self:
            start = record.date_from
            end = record.date_to
            employee = record.employee_id.id

            query = 'select a."number" as kode, ' \
                    'd.name_related as khl, ' \
                    'c.total_payslip as upah, ' \
                    'g.total_bkm as bkm, ' \
                    '(g.total_bkm-c.total_payslip) as selisih ' \
                    'from hr_payslip a ' \
                    'left join ( ' \
                    '    select distinct b.slip_id, b.employee_id, sum(b.total) as total_payslip ' \
                    '    from hr_payslip_line b ' \
                    '    where b.code in (\'EDW\',\'PR\',\'PRWD\',\'OT\') ' \
                    '   group by b.slip_id, b.employee_id ' \
                    '   ) as c on c.slip_id = a.id ' \
                    'left join hr_employee d on d.id = a.employee_id ' \
                    'left join ( ' \
                    '    select f.employee_id, sum(f.amount) as total_bkm ' \
                    '    from estate_upkeep_labour f ' \
                    '   where ' \
                    '        f.upkeep_date between \'%s\' ' \
                    '        and \'%s\' ' \
                    '       and f.state = \'approved\' ' \
                    '        group by f.employee_id ' \
                    '    ) as g on g.employee_id = a.employee_id ' \
                    'where ' \
                    '    a.date_from >= \'%s\' ' \
                    '    and a.date_to <= \'%s\' ' \
                    '    and c.total_payslip::numeric != g.total_bkm::numeric ' \
                    '    and a.employee_id = %s ' \
                    'order by d.name_related asc ' % (start, end, start, end, employee)
            self._cr.execute(query)
            res = self._cr.dictfetchall()
            return {k:v for x in res for k,v in x.items()}

    @api.multi
    def _check_payslip_company(self):
        """ Check if employe company is match payslip run company. It happened when employee was moved within period."""
        for record in self:
            start = record.date_from
            end = record.date_to
            employee = record.employee_id.id

            query = 'select ' \
                    '   a.id, ' \
                    '   a.payslip_run_id "payslip_run_id", ' \
                    '   d."name" "payslip_run_name", ' \
                    '   c."name" "team", ' \
                    '   b.name_related as "khl", ' \
                    '   b.nik_number "nik", ' \
                    '   e."name" "company_payslip", ' \
                    '   f."name" "company_employee", ' \
                    '   d.create_date "payslip_run_date", ' \
                    '   b.write_date "employee_update_date" ' \
                    'from hr_payslip a ' \
                    'left join hr_employee b on b.id = a.employee_id ' \
                    'left join estate_hr_team c on c.id = a.team_id ' \
                    'left join hr_payslip_run d on d.id = a.payslip_run_id ' \
                    'left join res_company e on e.id = d.company_id ' \
                    'left join res_company f on f.id = b.company_id ' \
                    'where '\
                    '   d.company_id != b.company_id ' \
                    '   and a.date_from >= \'%s\' ' \
                    '   and a.date_to <= \'%s\' ' \
                    '   and a.employee_id = %s ' \
                    'order by f.id, b.name_related; ' % (start, end, employee)

            self._cr.execute(query)
            res = self._cr.dictfetchall()
            return {k:v for x in res for k,v in x.items()}

    @api.multi
    def check_payslip(self):
        """ Wrapper for sanity check for single payslip
        1. Labor has no team.
        2. BKM vs. payslip.
        3. Empty attendance code.
        4. Wrong salary rule.
        """
        # payslip_ids = self.query_wage_no_team(self.date_start, self.date_end).mapped('khl')
        # if payslip_ids:
        #     err_msg = _('There are %d payslip which has no team.\n' \
        #                 'Please check if these name(s) %s has team' % (len(payslip_ids), payslip_ids))
        #     raise ValidationError(err_msg)
        res = {}
        for record in self:
            res['employee'] = record.employee_id.name
            res['team'] = record._check_payslip_team()
            # do not check wage - recompute is to maintain payslip integrity with upkeep.
            # res['wage'] = record._check_payslip_wage()
            res['company'] = record._check_payslip_company()
        return res

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """Contract type Estate Worker use upkeep labour number of days.
        Get worked days from upkeep labour with number_of_day > 0 after estate assistant confirmed
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        upkeep_labour_obj = self.env['estate.upkeep.labour']
        res = []

        # Check contract if any (before payslip date start)
        for contract in self.env['hr.contract'].search([('id', 'in', contract_ids),
                                                        ('date_start', '<=', date_from)],
                                                       limit=1,
                                                       order='date_start desc'):

            if contract.type_id.name == _("Estate Worker"):  #todo change to external id
                upkeep_labour_ids = upkeep_labour_obj.search([('employee_id', '=', contract.employee_id.id),
                                                              ('upkeep_date', '>=', date_from),
                                                              ('upkeep_date', '<=', date_to),
                                                              ('state', 'in', ['confirmed', 'approved'])]).ids

                # Get worked days
                att_number_of_days = upkeep_labour_obj.get_worked_days(upkeep_labour_ids)
                att_hour = upkeep_labour_obj.get_workhour(upkeep_labour_ids)
                if att_number_of_days:
                    attendances = {
                        'name': _("Estate Upkeep Working Days paid at 100%"),
                        'sequence': 1,
                        'code': 'WORK300',
                        'number_of_days': att_number_of_days,
                        'number_of_hours': att_hour,
                        'contract_id': contract.id,
                    }
                    res += [attendances]

                # Get piece rate worked days
                piece_rate_worked_days = upkeep_labour_obj.get_piece_rate_worked_days(upkeep_labour_ids)
                piece_rate_hour = upkeep_labour_obj.get_piece_rate_workhour(upkeep_labour_ids)
                if piece_rate_worked_days:
                    attendances = {
                        'name': _("Piece Rate Working Days"),
                        'sequence': 2,
                        'code': 'WORK310',
                        'number_of_days': piece_rate_worked_days,
                        'number_of_hours': piece_rate_hour,
                        'contract_id': contract.id,
                    }
                    res += [attendances]

                return res
            else:
                return super(Payslip, self).get_worked_day_lines(contract_ids, date_from, date_to)

    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        """Contract type Estate Worker use upkeep labour overtime and piece rate. after estate assistant confirmed
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        upkeep_labour_obj = self.env['estate.upkeep.labour']
        att_obj = self.env['hr.attendance']
        res = []

        # Check contract if any (before payslip date start)
        labour_contract_ids = self.env['hr.contract'].search([('id', 'in', contract_ids),
                                                              ('date_start', '<=', date_from)],
                                                             limit=1,
                                                             order='date_start desc')
        
        if not len(labour_contract_ids):
            err_msg = _('Please check all employee contract date should be in period of payroll batch.')
            raise ValidationError(err_msg)

        for contract in labour_contract_ids:
            if contract.type_id.name == _("Estate Worker"):  #todo change to external id
                upkeep_labour_ids = upkeep_labour_obj.search([('employee_id', '=', contract.employee_id.id),
                                                              ('upkeep_date', '>=', date_from),
                                                              ('upkeep_date', '<=', date_to),
                                                              ('state', 'in', ['confirmed', 'approved'])]).ids

                # Get Overtime
                overtime_amount = upkeep_labour_obj.get_wage_overtime(upkeep_labour_ids)
                if overtime_amount:
                    overtime = {
                        'name': _("Overtime"),
                        'code': _("OT"),
                        'contract_id': contract.id,
                        'amount': overtime_amount
                    }
                    res += [overtime]

                # Get Piece Rate
                piece_rate_amount = upkeep_labour_obj.get_wage_piece_rate(upkeep_labour_ids)
                if piece_rate_amount:
                    piece_rate = {
                        'name': _("Piece Rate"),
                        'code': _("PR"),
                        'contract_id': contract.id,
                        'amount': piece_rate_amount
                    }
                    res += [piece_rate]
                return res
            else:
                return super(Payslip, self).get_inputs(contract_ids, date_from, date_to)

    # @api.multi
    # def get_wage_overtime(self, ids):
    #     """
    #     Amount of piece rate required by salary rules
    #     :param ids: upkeep labour
    #     :return: wage overtime
    #     """
    #     amount = 0.00
    #
    #     for record in self.env['estate.upkeep.labour'].search([('id', 'in', ids)]):
    #         amount += record['wage_overtime']
    #     return amount

    @api.multi
    def action_open_labour(self):
        """HR cross check related upkeep labour before and after payslip
        """
        context = self._context.copy()
        view_id = self.env.ref('estate_payroll.payslip_upkeep_labour_view_tree').id

        # Payslip only processed approved upkeep labour of selected employee within payslip period

        upkeep_labour_filter = [('id', 'in', self._get_upkeep_labour())]

        res = {
            'name': _('Upkeep Labour Records %s' % self.employee_id.name),
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(view_id, 'tree')],
            'res_model': 'estate.upkeep.labour',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context': context,
            'domain': upkeep_labour_filter,
        }

        return res

    @api.multi
    def recompute_sheet(self):
        """ Resolve payslip calculation: upkeep weekly closing, employee without contract."""
        no_contract = []
        summary = []
        for record in self:

            # prevent recompute for non draft
            if record.state != 'draft':
                continue

            # notify user if there was employee without contract
            if not record.contract_id:
                no_contract.append(record.employee_id.name_related)

            # trigger computed field
            record._get_team()
            record.onchange_employee()  # reset worked days and inputs line.
            record.compute_sheet()

            # sanity check payslip
            res = record.check_payslip()
            if res: summary.append(res)

        # display employee with problem
        team = []
        company = []

        for x in summary:
            if x['team']:
                team.append(x['team']['khl'])
            if x['company']:
                company.append(x['company']['khl'])

        # display different message when called from singleton
        if len(summary) == 1:
            err_msg = _('There are problem with %s payslip.\n\n'
                        '1. Labour did not registered at any team.\n'
                        '3. Difference at company (payslip run to employee)' % (record.employee_id.name))
        else:
            err_msg = _('There are problem with our payslip.\n\n'
                        'Labour without team: %s\n '
                        'Difference at company: %s' % (', '.join(team),
                                                       ', '.join(company)))

        if len(team) or len(company):
            # Assign team or fix employee company to match payslip run.
            raise ValidationError(err_msg)

        # notify at the end of process
        if no_contract:
            err_msg = _('You have %s employee(s) without contract. Name: %s' % (len(set(no_contract)),
                                                                                ", ".join(set(no_contract))))
            raise ValidationError(err_msg)


    @api.multi
    def compute_sheet_all(self):
        """ Resolve compute sheet of payslips from tree view."""
        for record in self:
            record.compute_sheet()
        return

    @api.model
    def create(self, vals):
        """ Set payslip company based on employee's company."""
        company_id = self.env['hr.employee'].search([('id', '=', vals['employee_id'])]).company_id
        vals['company_id'] = company_id.id
        return super(Payslip, self).create(vals)

