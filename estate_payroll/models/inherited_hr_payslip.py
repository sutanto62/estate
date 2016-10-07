# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
from openerp.tools.translate import _

class Payslip(models.Model):
    """
    Prepare payslip's worked day and input lines.
    """
    _inherit = 'hr.payslip'

    team_id = fields.Many2one('estate.hr.team', 'Team', compute='_get_team', store=True, help="Employee's original Team")
    payroll_location_id = fields.Many2one(related='team_id.payroll_location_id',
                                          store=True, readonly=True)
    contract_type_id = fields.Many2one(related='contract_id.type_id', readonly=True)
    upkeep_labour_count = fields.Integer(compute='_compute_upkeep_labour', string='Payslip Upkeep Labour Details')

    #@api.multi
    @api.depends('employee_id')
    def _get_team(self):
        """Estate worker's payslip disbursed per team
        """
        for payslip in self:
            for member in self.env['estate.hr.member'].search([('employee_id', '=', payslip.employee_id.id)], limit=1):
                if member.team_id.state != 'draft':
                    payslip.team_id = member.team_id.id
                    return True
                else:
                    return False

    @api.multi
    def _compute_upkeep_labour(self):
        """ Display number of upkeep did by the labour in payslip """
        upkeep_labour_obj = self.env['estate.upkeep.labour']
        res = upkeep_labour_obj.search([('upkeep_date', '>=', self.date_from),
                                        ('upkeep_date', '<=', self.date_to),
                                        ('employee_id', '=', self.employee_id.id),
                                        ('state', '=', 'approved')])
        self.upkeep_labour_count = len(res)

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """Contract type Estate Worker use upkeep labour number of days.
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
                attendances = {
                     'name': _("Estate Upkeep Working Days paid at 100%"),
                     'sequence': 1,
                     'code': 'WORK300',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
                upkeep_labour_ids = upkeep_labour_obj.search([('employee_id', '=', contract.employee_id.id),
                                                              ('upkeep_date', '>=', date_from),
                                                              ('upkeep_date', '<=', date_to),
                                                              ('state', '=', 'approved')]).ids
                attendances['number_of_days'] = upkeep_labour_obj.get_worked_days(upkeep_labour_ids)
                attendances['number_of_hours'] = upkeep_labour_obj.get_workhour(upkeep_labour_ids)
                res += [attendances]
                return res
            else:
                return super(Payslip, self).get_worked_day_lines(contract_ids, date_from, date_to)

    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        """Contract type Estate Worker use upkeep labour overtime and piece rate.
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        upkeep_labour_obj = self.env['estate.upkeep.labour']
        att_obj = self.env['hr.attendance']
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
                                                              ('state', '=', 'approved')]).ids

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
        """HR cross check related upkeep labour
        """
        context = self._context.copy()
        view_id = self.env.ref('estate.upkeep_labour_view_tree').id

        # Payslip only processed approved upkeep labour of selected employee within payslip period
        upkeep_labour_filter = [('employee_id', '=', self.employee_id.id),
                                ('upkeep_date', '>=', self.date_from),
                                ('upkeep_date', '<=', self.date_to),
                                ('state', '=', 'approved')]

        res = {
            'name': _('Upkeep Labour Records %s' % self.employee_id.name),
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(view_id, 'tree')],
            'res_model': 'estate.upkeep.labour',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context': context,
            'domain': upkeep_labour_filter
        }

        return res