# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv
from datetime import datetime

ESTATE_LOCATION_LEVEL = [('1', 'Estate'), ('2','Division'), ('3', 'Block'), ('4', 'Sub Block')]
ESTATE_LOCATION_TYPE = [('nursery', 'Nursery'), ('planted', 'Planted'), ('emplacement', 'Emplacement')]
STATE = [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('revised', 'Revised'), ('done', 'Done')]

class MonthlyPlan(models.Model):
    _name = 'estate.plan.monthly'
    _rec_name = 'complete_name'
    _order = 'date_year,date_month'

    name = fields.Char("Name")
    complete_name = fields.Char("Complete Name", compute='_get_full_name', store=True   )
    user_responsible = fields.Many2one('res.users', "Responsible User", help='Fill in Assistant Name')  # todo filter by job group (assistant).
    user_approver = fields.Many2one('res.users', "Approver User")  # todo filter by job group (manager).
    active = fields.Boolean("Active", default='True')
    date_effective = fields.Date('Effective Date', help='Fill in with a start date')
    date_month = fields.Integer('Month', compute='_compute_date', store=True)
    date_year = fields.Integer('Year', compute='_compute_date', store=True)
    estate_location_level = fields.Selection(ESTATE_LOCATION_LEVEL, "Planning Level",
                                             required=True, default = '1',
                                             help="""The Planning Level define cost center level (Estate, Division,
                                             or Estate).
                                             """)
    estate_location_type = fields.Selection(ESTATE_LOCATION_TYPE, "Planning Type",
                                            required=True, default="planted",
                                            help="""The Planning Type define cost center type (Nursery, Planted or
                                            Emplacement).
                                            """)
    state = fields.Selection(STATE, default='draft')
    activity_ids = fields.One2many('estate.plan.activity', 'plan_id')

    @api.depends('date_effective')
    def _compute_date(self):
        if self.date_effective:
            d = self.date_effective
            ds = datetime.strptime(d, '%Y-%m-%d')
            self.date_month = ds.month
            self.date_year = ds.year
        return 1

    @api.depends('date_effective')
    def _get_full_name(self):
        if self.date_effective:
            title = 'RKB' + '/' + str(self.date_year) + '/' + str(self.date_month)
            self.complete_name = title.upper()
        return 1

class ActivitiesPlan(models.TransientModel):
    _name = 'estate.plan.activities'

    plan_id = fields.Many2one('estate.plan.monthly')
    activity_id = fields.Many2one('estate.activity')
    location_ids = fields.One2many('estate.plan.locations', 'activities_id')

class ActivitiesLocations(models.TransientModel):
    _name = 'estate.plan.locations'

    activities_id = fields.Many2one('estate.plan.activities')
    location_id = fields.Many2one('stock.location')

class ActivityPlan(models.Model):
    _name = 'estate.plan.activity'

    name = fields.Char('Name')
    plan_id = fields.Many2one('estate.plan.monthly')
    activity_id = fields.Many2one('estate.activity')
    location_id = fields.Many2one('stock.location')
    qty_target = fields.Float('Target')
    qty_target_uom = fields.Many2one('product.uom')
    account_expense_id = fields.Many2one('account.account')
    material_ids = fields.One2many('estate.plan.material', 'activity_id')
    labour_ids = fields.One2many('estate.plan.labour', 'activity_id')
    comment = fields.Text('Additional Information')

class ActivityMaterial(models.Model):
    _name = 'estate.plan.material'

    activity_id = fields.Many2one('estate.plan.activity')
    product_id = fields.Many2one('product.product', 'Product')
    qty_standard = fields.Float('Standard Quantity', help='Required material based on Activity\'s Standard')
    qty = fields.Float('Quantity')
    uom_usage_id = fields.Many2one('product.uom', 'Unit of Usage')

class ActivityLabour(models.Model):
    _name = 'estate.plan.labour'

    activity_id = fields.Many2one('estate.plan.activity')
    labour_type_id = fields.Many2one('estate.labour.type', 'Labour Type')
    qty = fields.Integer('Labour Quantity')
    wages = fields.Float('Labour Wages', help='Amount of wages in standard currency.')





