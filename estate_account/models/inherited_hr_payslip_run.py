# -*- coding: utf-8 -*-

import logging
from openerp import models, fields, api, exceptions, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class PayslipRun(models.Model):
    """Create journal entries
    """
    _inherit = 'hr.payslip.run'

    state = fields.Selection(selection_add=[('journaled', 'Journaled')])
    # accrued_journal_id = fields.Many2one('account.journal', 'Payroll Accrued Journal', required=True,
    #                              domain="[('type','=','general'),('company_id', '=', company_id)]")
    # allocation_journal_id = fields.Many2one('account.journal', 'Payroll Allocation', required=True,
    #                                       domain="[('type','=','general'), ('company_id', '=', company_id)]")
    # receivable_journal_id = fields.Many2one('account.journal', 'Receivable', required=True,
    #                                         domain="[('type', '=', 'general'), ('company_id', '=', company_id)]")

    @api.multi
    def get_debit_name(self, vals):
        """Account move name depends on employee company and location company"""
        for payslip_run in self:
            rec_employee = vals['employee_company_id']
            rec_company = vals['company_id']
            company_id = self.env['res.company'].browse(vals['company_id'])
            cost_category_id = self.env['estate_account.payroll_cost_category'].browse(vals['id'])
            if rec_employee and rec_company:
                if rec_employee == rec_company:
                    val = _('%s %s ' % (cost_category_id.name, payslip_run.name))
                else:
                    val = _('%s %s for %s' % (cost_category_id.name, payslip_run.name, company_id.code))
                return val

    @api.multi
    def get_credit_name(self):
        for record in self:
            return _('Payroll %s' % record.name)

    @api.multi
    def get_line_name(self, line, number_of_day=False, line_date=False):
        """ User required to view number of day and month year"""
        self.ensure_one()
        lang = self.env['res.lang'].search([('code','=', self.env.user.lang)])
        name = []
        name.append(line)
        if number_of_day:
            # postgres use period (.) for decimal
            name.append('HK ' + str(number_of_day).replace('.', lang.decimal_point))
        if line_date:
            line_date = datetime.strptime(line_date, DEFAULT_SERVER_DATE_FORMAT)
            name.append(line_date.strftime("%m %y"))
        return ' '.join(str(e) for e in name)

    @api.multi
    def get_employee_ids(self):
        """ Create account move based on registered employee at payslip"""
        for record in self:
            employee_ids = []
            for slip in record.slip_ids:
                employee_ids.append(slip.employee_id.id)

            res = ", ".join(str(x) for x in employee_ids)

            return res

    @api.multi
    def get_payroll_category(self):
        self.ensure_one()
        payroll_cost_category_ids = self.env['estate_account.payroll_cost_category'].search([('active', '=', 'True')])

        if not payroll_cost_category_ids:
            err_msg = _('You have not defined Accrued Category and Labour Account.')
            raise exceptions.ValidationError(err_msg)

        case = []
        for item in payroll_cost_category_ids:
            case.append("when c.code = '%s' then %s" % (item.code, item.aggregation))

        return case

    @api.multi
    def create_accrued(self, batch):
        """
        Multiple debit move line - allocation cost control.
        Single credit move line - allocation cost control.
        Args:
            batch: payslip run
        """
        self.ensure_one()

        # accrued payroll journal
        journal_id = self.env['account.journal'].search([('code', '=', 'GAJI'),
                                                         ('company_id', '=', batch.company_id.id)],
                                                        limit=1)

        # error update modules
        if not journal_id:
            err_msg = _('Unable to close payslips batches.\n'\
                        'No Accounting Journals for payroll configured.')
            raise exceptions.ValidationError(err_msg)

        payroll_cost_category_ids = self.env['estate_account.payroll_cost_category'].browse()
        precision = self.env['decimal.precision'].precision_get('Payroll')
        move_obj = self.env['account.move']
        move_line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0

        if batch.state != 'close':
            pass

        vals = {
            'journal_id': journal_id.id,
            'company_id': batch.company_id.id,
            'partner_id': batch.company_id.partner_id.id,
            'date': batch.date_end,
            'ref': batch.name,
        }

        # get approved upkeep labour
        query = """
                select
                    b.contract_type,
                    b.contract_period,
                    c.id,
                    a.employee_company_id,
                    a.company_id,
                    (
                        select
                            d.account_id
                        from estate_account_payroll_cost d
                        where
                            d.contract_type = b.contract_type
                            and d.contract_period = b.contract_period
                            and d.category_id = c.id
                            and d.company_id = %d
                    ) as "account_id",
                    case
                        %s
                    end as "amount"
                from estate_upkeep_labour a cross join estate_account_payroll_cost_category c
                left join hr_employee b on b.id = a.employee_id
                where
                    a.upkeep_date between '%s' and '%s'
                    and a.state in ('approved', 'correction', 'payslip')
                    and a.employee_id in (%s)
                group by b.contract_type, contract_period, c.id, a.employee_company_id, a.company_id
                order by b.contract_type, b.contract_period, c.id, a.employee_company_id, a.company_id
                """ % (batch.company_id.id,
                       " ".join(batch.get_payroll_category()),
                       batch.date_start,
                       batch.date_end,
                       batch.get_employee_ids())

        self.env.cr.execute(query)
        res = self.env.cr.dictfetchall()

        # check debit account move line
        if not res:
            err_msg = _('Unable to close payslips batches. No payroll cost setup available.')
            raise exceptions.ValidationError(err_msg)

        # debit account move line to be checked with allocation cost
        for line in res:
            debit_account_id = line['account_id']
            employee_company_id = line['employee_company_id']
            company_id = line['company_id']

            # avoid unbalance move line caused by incomplete data
            if debit_account_id and employee_company_id and company_id:
                debit_line = (0, 0, {
                    'name': self.get_line_name(batch.get_debit_name(line), False, batch.date_end),
                    'partner_id': batch.company_id.partner_id.id,
                    'account_id': debit_account_id,
                    'accrued_journal_id': journal_id.id,
                    'date': batch.date_end,
                    'debit': line['amount'],
                    'credit': 0,
                })

                # ignore empty move
                if debit_line[2]['debit']:
                    move_line_ids.append(debit_line)

                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
                credit_sum = debit_sum

        # credit account move line - summarized
        credit_line = (0, 0, {
            'name': self.get_line_name(batch.get_credit_name(), False, batch.date_end),
            'partner_id': batch.company_id.partner_id.id,
            'account_id': journal_id.default_credit_account_id.id,
            'journal_id': journal_id.id,
            'date': batch.date_end,
            'debit': 0,
            'credit': credit_sum,
        })

        # ignore empty move
        if credit_line[2]['credit']:
            move_line_ids.append(credit_line)

        vals['line_ids'] = move_line_ids

        move_id = move_obj.create(vals)
        move_id.post()

        self.create_bank(batch, credit_sum)

        return True

    @api.multi
    def create_bank(self, batch, credit):
        """ Create payroll bank account from accrued."""

        move_obj = self.env['account.move']
        move_line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        credit_sum = credit
        account_name = batch.get_credit_name()

        journal_id = self.env['account.journal'].search([('code', '=', 'GBNK'),
                                                         ('company_id', '=', batch.company_id.id)],
                                                        limit=1)
        # error update modules
        if not journal_id:
            err_msg = _('Unable to close payslips batches.\n' \
                        'No Accounting Journals for payroll configured.')
            raise exceptions.ValidationError(err_msg)

        vals = {
            'journal_id': journal_id.id,
            'company_id': batch.company_id.id,
            'partner_id': batch.company_id.partner_id.id,
            'date': batch.date_end,
            'ref': batch.name,
        }

        # create account move line for bank
        payroll_bank_debit_sum = credit_sum
        bank_debit_line = (0, 0, {
            'name': self.get_line_name(account_name, False, batch.date_end),
            'partner_id': batch.company_id.partner_id.id,
            'account_id': journal_id.default_debit_account_id.id,
            'journal_id': journal_id.id,
            'date': batch.date_end,
            'debit': payroll_bank_debit_sum,
            'credit': 0,
        })

        move_line_ids.append(bank_debit_line)

        company_account_obj = self.env['estate_account.company_account']
        default_account_id = company_account_obj.search([('default', '=', True)], limit=1)
        company_account_id = company_account_obj.search([('company_id', '=', batch.company_id.id)])
        if default_account_id:
            bank_account_id = default_account_id.credit_id
        else:
            bank_account_id = company_account_id.credit_id

        if not bank_account_id:
            err_msg = _('No Payroll Bank Account defined.')
            raise exceptions.ValidationError(err_msg)

        # setup account id at journal
        bank_credit_line = (0, 0, {
            'name': self.get_line_name(account_name, False, batch.date_end),
            'partner_id': batch.company_id.partner_id.id,
            'account_id': bank_account_id.id,
            'journal_id': journal_id.id,
            'date': batch.date_end,
            'debit': 0,
            'credit': credit_sum,
        })

        move_line_ids.append(bank_credit_line)

        vals['line_ids'] = move_line_ids

        move_id = move_obj.create(vals)
        move_id.post()

        return True

    @api.multi
    def create_allocation(self, batch):
        self.ensure_one()

        move_obj = self.env['account.move']
        debit_sum = 0.0
        credit_sum = 0.0
        move_line_ids = []
        journal_id = self.env['account.journal'].search([('code', '=', 'GTRN'),
                                                         ('company_id', '=', batch.company_id.id)],
                                                        limit=1)

        # error update modules
        if not journal_id:
            err_msg = _('Unable to close payslips batches.\n' \
                        'No Accounting Journals for payroll configured.')
            raise exceptions.ValidationError(err_msg)

        vals = {
            'journal_id': journal_id.id,
            'company_id': batch.company_id.id,
            'partner_id': batch.company_id.partner_id.id,
            'date': batch.date_end,
            'ref': batch.name,
        }

        # get approved upkeep labour
        query = """
                select
                    a.company_id "company",
                    e.name "activity",
                    a.general_account_id "general_account",
                    b.name "general_account_name",
                    d.analytic_account_id "analytic_account",
                    sum(a.number_of_day) "number_of_day",
                    sum(wage_number_of_day+wage_overtime+wage_piece_rate) "amount"
                from estate_upkeep_labour a
                left join account_account b on b.id = a.general_account_id
                left join estate_block_template c on c.id = a.location_id
                left join estate_planted_year d on d.id = c.planted_year_id
                left join estate_activity e on e.id = a.activity_id
                where
                    a.upkeep_date between '%s' and '%s'
                    and a.company_id = %d
                    and a.state in ('approved', 'correction', 'payslip')
                    and a.employee_id in (%s)
                group by a.company_id, e.name, a.general_account_id, b.name, d.analytic_account_id
                order by a.company_id, e.name, a.general_account_id, b.name, d.analytic_account_id
                """ % (batch.date_start,
                       batch.date_end,
                       batch.company_id.id,
                       batch.get_employee_ids())

        self.env.cr.execute(query)
        res = self.env.cr.dictfetchall()

        if not res:
            err_msg = _('No accrued allocation will be created.')
            raise exceptions.ValidationError(err_msg)

        # check debit account move line
        for line in res:

            # make sure analytic_account_id return True or False
            analytic_account_id = line['analytic_account'] if line['analytic_account'] is not None else False

            # show message if no account
            if not line['general_account']:
                err_msg = _('Activity %s has no general account.\n'\
                            'Please check your account configuration.' % line['activity'])
                raise exceptions.ValidationError(err_msg)

            # create move line for current company
            debit_line = (0, 0, {
                'name': self.get_line_name(line['general_account_name'],
                                           line['number_of_day'],
                                           batch.date_end),
                'partner_id': batch.company_id.partner_id.id,
                'account_id': line['general_account'],
                'analytic_account_id': analytic_account_id,
                'journal_id': journal_id.id,
                'date': batch.date_end,
                'debit': line['amount'],
                'credit': 0,
            })

            # avoid posting activity without general account
            if not debit_line[2]['name']:
                err_msg = _('Cannot create journal entries for %s - account not defined yet.' % line['activity'])
                raise exceptions.ValidationError(err_msg)

            # ignore empty move
            if debit_line[2]['debit']:
                move_line_ids.append(debit_line)

            debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

        # credit account move line - summarized
        credit_sum = debit_sum
        credit_line = (0, 0, {
            'name': self.get_line_name(batch.get_credit_name(), False, batch.date_end),
            'partner_id': batch.company_id.partner_id.id,
            'account_id': journal_id.default_credit_account_id.id,
            'journal_id': journal_id.id,
            'date': batch.date_end,
            'debit': 0,
            'credit': credit_sum,
        })

        # ignore empty move
        if credit_line[2]['credit']:
            move_line_ids.append(credit_line)


        vals['line_ids'] = move_line_ids

        move_id = move_obj.create(vals)
        move_id.post()

        return True

    @api.multi
    def create_payable_allocation(self, batch):
        """ Payable allocation recorded at location company account which was not belong to batch company."""

        self.ensure_one()

        move_obj = self.env['account.move']

        query = """
                select distinct
                    a.company_id "company"
                from estate_upkeep_labour a
                where
                    a.upkeep_date between '%s' and '%s'
                    and a.company_id != %d
                    and a.state in ('approved', 'correction', 'payslip')
                    and a.employee_id in (%s)
                """ % (batch.date_start,
                       batch.date_end,
                       batch.company_id.id,
                       batch.get_employee_ids())

        self.env.cr.execute(query)
        res_company = self.env.cr.dictfetchall()

        for company in res_company:

            # reset vals and move_line_ids
            vals = []
            debit_sum = 0.0
            credit_sum = 0.0
            move_line_ids = []

            # Create allocation journal (with payable credit move line)
            company_id = self.env['res.company'].browse([company['company']])
            partner_id = company_id.partner_id

            # account move used journal's company
            journal_id = self.env['account.journal'].search([('code', 'like', 'GTRA'),
                                                             ('company_id', '=', company_id.id)],
                                                            limit=1)
            if not journal_id:
                err_msg = _('No journal for ')
                return exceptions.ValidationError(err_msg)

            vals = {
                'journal_id': journal_id.id,
                'company_id': company_id.id,
                'partner_id': partner_id.id,
                'date': batch.date_end,
                'ref': batch.name,
            }

            query = """
                    select
                        a.company_id "company",
                        a.general_account_id "general_account",
                        b.name "general_account_name",
                        d.analytic_account_id "analytic_account",
                        sum(a.number_of_day) "number_of_day",
                        sum(wage_number_of_day+wage_overtime+wage_piece_rate) "amount"
                    from estate_upkeep_labour a
                    left join account_account b on b.id = a.general_account_id
                    left join estate_block_template c on c.id = a.location_id
                    left join estate_planted_year d on d.id = c.planted_year_id
                    where
                        a.upkeep_date between '%s' and '%s'
                        and a.company_id = %d
                        and a.state in ('approved', 'correction', 'payslip')
                        and a.employee_id in (%s)
                    group by a.company_id,  a.general_account_id, b.name, d.analytic_account_id
                    order by a.company_id,  a.general_account_id, b.name, d.analytic_account_id
                    """ % (batch.date_start,
                           batch.date_end,
                           company_id.id,
                           batch.get_employee_ids())

            self.env.cr.execute(query)
            res = self.env.cr.dictfetchall()

            for line in res:
                debit_account_id = self.env['account.account'].browse([line['general_account']])

                # make sure analytic_account_id return True or False
                analytic_account_id = line['analytic_account'] if line['analytic_account'] is not None else False

                # create move line for different company
                debit_line = (0, 0, {
                    'name': self.get_line_name(line['general_account_name'],
                                               line['number_of_day'],
                                               batch.date_end),
                    'partner_id': company_id.partner_id.id,
                    'account_id': debit_account_id.id,
                    'analytic_account_id':  analytic_account_id,
                    'journal_id': journal_id.id,
                    'date': batch.date_end,
                    'debit': line['amount'],
                    'credit': 0,
                })

                move_line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

            # credit line
            credit_sum = debit_sum
            credit_account_id = self.env['account.account'].search([('company_id', '=', company_id.id),
                                                                    ('name', 'like', batch.company_id.code)],
                                                                   limit=1)

            if not credit_account_id:
                err_msg = _('%s has no payable account.' % company_id.name)
                raise exceptions.ValidationError(err_msg)

            credit_line = (0, 0, {
                'name': self.get_line_name(credit_account_id.name, False, batch.date_end),
                'partner_id': company_id.partner_id.id,
                'account_id': credit_account_id.id,
                'journal_id': journal_id.id,
                'date': batch.date_end,
                'debit': 0,
                'credit': credit_sum,
            })
            move_line_ids.append(credit_line)

            vals['line_ids'] = move_line_ids

            move_id = move_obj.create(vals)
            move_id.with_context(check_move_validity=False).post()

        return True

    @api.multi
    def create_receivable(self, batch):
        """Receivable should be included in allocation move line."""

        self.ensure_one()

        move_obj = self.env['account.move']
        receivable_line_ids = []

        journal_id = self.env['account.journal'].search([('code', '=', 'GPAP'),
                                                         ('company_id', '=', batch.company_id.id)],
                                                        limit=1)

        # error update modules
        if not journal_id:
            err_msg = _('Unable to close payslips batches.\n' \
                        'No Accounting Journals for payroll configured.')
            raise exceptions.ValidationError(err_msg)

        if not journal_id:
            err_msg = _('No journal for ')
            return exceptions.ValidationError(err_msg)

        vals = {
            'journal_id': journal_id.id,
            'company_id': batch.company_id.id,
            'partner_id': False,
            'date': batch.date_end,
            'ref': batch.name,
        }

        # get approved upkeep labour
        query = """
                select
                    a.company_id "company",
                    sum(wage_number_of_day+wage_overtime+wage_piece_rate) "amount"
                from estate_upkeep_labour a
                left join account_account b on b.id = a.general_account_id
                where
                    a.upkeep_date between '%s' and '%s'
                    and a.company_id != %d
                    and a.state in ('approved', 'correction', 'payslip')
                    and a.employee_id in (%s)
                group by a.company_id
                order by a.company_id
                """ % (batch.date_start,
                       batch.date_end,
                       batch.company_id.id,
                       batch.get_employee_ids())

        self.env.cr.execute(query)
        res = self.env.cr.dictfetchall()

        # current payroll batch contained no different company
        if not res:
            return True

        # check debit account move line
        for line in res:
            receivable_company_id = self.env['res.company'].browse([line['company']])
            partner_id = self.env['res.partner'].browse([receivable_company_id.partner_id.id])

            # create move line for current company
            # TODO change receivable account based on company
            debit_line = (0, 0, {
                'name': self.get_line_name(journal_id.default_debit_account_id.name + " " + receivable_company_id.code,
                                           False,
                                           batch.date_end),
                'partner_id': partner_id.id,
                'account_id': journal_id.default_debit_account_id.id,
                'journal_id': journal_id.id,
                'date': batch.date_end,
                'debit': line['amount'],
                'credit': 0,
            })
            receivable_line_ids.append(debit_line)

            credit_line = (0, 0, {
                'name': self.get_line_name(journal_id.default_credit_account_id.name + " " + receivable_company_id.code,
                                           False,
                                           batch.date_end),
                'partner_id': batch.company_id.partner_id.id,
                'account_id': journal_id.default_credit_account_id.id,
                'journal_id': journal_id.id,
                'date': batch.date_end,
                'debit': 0,
                'credit': line['amount'],
            })
            receivable_line_ids.append(credit_line)

        vals['line_ids'] = receivable_line_ids

        move_id = move_obj.create(vals)
        move_id.post()

        return True

    @api.multi
    def close_payslip_run(self):
        """
        Journal entry created before payroll closed. Avoid unbalance move line.
        Only include: wage number of day, wage overtime, wage piece rate.
        Not included yet: adjustment, deduction, tax, insurance, etc.
        :return: True
        """

        for record in self:
            self.create_accrued(record)
            self.create_allocation(record)
            self.create_receivable(record)
            self.create_payable_allocation(record)

            super(PayslipRun, record).close_payslip_run()

            record.state = 'journaled'

            return record

