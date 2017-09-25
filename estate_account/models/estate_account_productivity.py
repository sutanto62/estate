# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv, _

# deprecated record when journaled at move line.
class EstateAccountProductivity(models.Model):
    _name = 'estate_account.productivity'
    _description = 'Estate Account Productivity'

    company_id = fields.Many2one('res.company', 'Company')
    analytic_account_id =  fields.Many2one('account.analytic.account', 'Analytic Account')
    general_account_id = fields.Many2one('account.account', 'General Account')
    quantity = fields.Float('Quantity')
    amount_number_of_day = fields.Float('Number of Day Amount')
    amount_overtime = fields.Float('Overtime Amount')
    amount_piece_rate = fields.Float('Piece Rate Amount')
    amount_material = fields.Float('Material Amount')
    sub_total = fields.Float('Sub Total Amount')

