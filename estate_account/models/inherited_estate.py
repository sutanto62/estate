# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv, _


class Activity(models.Model):

    _inherit = 'estate.activity'

    labour_account_id = fields.Many2one('account.account', 'Labour Account',
                                         help='Set as labour account.', track_visibility="onchange")
    material_account_id = fields.Many2one('account.account', 'Material Account',
                                         help='Set as material account.', track_visibility="onchange")
    other_account_id = fields.Many2one('account.account', 'Other Account',
                                         help='Set as contract works or VRA account.', track_visibility="onchange")
