# -*- coding: utf-8 -*-

from openerp import models, fields, api

class EstateConfigSettings(models.TransientModel):
    _name = 'estate.config.settings'
    _inherit = 'res.config.settings'

    module_estate_nursery = fields.Boolean("Seed Management",
                                           help="Record receiving from purchase order, planting and selection.")
    default_max_day = fields.Integer("Maximum day(s) backdate transaction entry",
                                     help="0 is today.",
                                     default_model='estate.upkeep',
                                     default=7)
    # Upkeep inherits account analytic entries - mandatory field
    default_journal_line_id = fields.Many2one('account.journal', 'Default Estate Journal',
                                             help='Used at upkeep analytic entries if no other journal defined.')
    default_analytic_account_id = fields.Many2one('account.analytic.account', 'Default Analytic Account',
                                            help='Used at upkeep analytic entries.')
    default_account_id = fields.Many2one('account.account', 'Default General Account',
                                            help='Used at upkeep analytic entries (expenses).')
    default_cross_team =fields.Boolean('Allow cross team labour record.')

    @api.model
    def get_default_journal(self, fields):
        config = self.env['estate.config.settings'].search([], order='id desc', limit=1)
        return {
            'default_journal_line_id': config.default_journal_line_id.id,
            'default_analytic_account_id': config.default_analytic_account_id.id,
            'default_account_id': config.default_account_id.id,
            'default_cross_team': config.default_cross_team,
            'default_max_day': config.default_max_day
        }

    @api.one
    def set_journal(self):
        config = self.env['estate.config.settings'].search([], order='id desc', limit=1)
        config.default_journal_line_id = self.default_journal_line_id.id
        config.default_analytic_account_id = self.default_analytic_account_id.id
        config.default_account_id = self.default_account_id.id
        config.default_cross_team = self.default_cross_team
        config.default_max_day = self.default_max_day
