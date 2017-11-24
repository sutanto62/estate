# -*- coding: utf-8 -*-

import logging
from openerp import models, api, fields

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def _post_validate(self):
        """ Error when post account move with different company."""
        if not self._context.get('check_move_validity'):
            self.assert_balanced()
            return self._check_lock_date()
        else:
            return super(AccountMove, self)._post_validate()

    @api.multi
    def action_journal_productivity(self):
        """ Update journal item productivity at account move.
        """
        for record in self:
            payslip_run_id = self.env['hr.payslip.run'].search([('name', '=', record.ref)])

            for line in record.line_ids:

                self.env['hr.payslip.run'].partner_general_account(line.account_id.id, line.partner_id.company_id.id)

                # account move recorded per activity
                query_activity_id = """
                                    select distinct a.activity_id as id
                                    from estate_upkeep_labour a
                                    join estate_planted_year b on b.id = a.planted_year_id
                                    join estate_activity c on c.id = a.activity_id
                                    where b.analytic_account_id = %d
                                    and a.general_account_id = %d
                                    and a.company_id = %d
                                    and a.activity_id = %d
                                    and c.is_productivity
                                    and upkeep_date between '%s' and '%s';
                                    """ % (line.analytic_account_id.id,
                                           line.account_id.id,
                                           line.company_id.id,
                                           line.activity_id.id,
                                           str(payslip_run_id.date_start),
                                           str(payslip_run_id.date_end))
                self._cr.execute(query_activity_id)
                activity_id = self._cr.dictfetchall()
                # don't waste time if journal has no analytic account
                if activity_id:
                    vals = {
                        'start': payslip_run_id.date_start,
                        'end': payslip_run_id.date_end,
                        'analytic': line.analytic_account_id.id or 0,
                        'account': line.account_id.id or 0,
                        'activity_id': activity_id[0]['id'],
                        'company': line.company_id.id or 0,
                    }
                    res = self.env['estate.upkeep.labour'].get_quantity(vals)
                else:
                    # error when journal item has no analytic
                    res = {'quantity':0.0, 'productivity_uom_id': ''}

                line.write({
                    'quantity': res['quantity'],
                    'product_uom_id': res['productivity_uom_id']
                })
            return True

    def account_productivity(self, vals):
        """
        Get account productivity when closing payslip.
        :param vals: domain
        :return: productivity
        :rtype: dict
        """

        account_prod = self.env['estate.upkeep.labour'].get_quantity(vals)
        res = {
            'quantity': account_prod['quantity'],
            'product_uom_id': account_prod['productivity_uom_id']
        }
        return res


class AccountMoveLine(models.Model):
    """ Update quantity and uom required activity"""
    _inherit = 'account.move.line'

    activity_id = fields.Many2one('estate.activity', 'Activity', help='Reverse search.',
                                  domain=[('type', '=', 'normal'), ('activity_type', '=', 'estate')])
