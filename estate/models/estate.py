# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv

class EstateLocation(models.Model):
    """Extend Location for Estate Location (Estate, Division, Block)"""
    _inherit = 'stock.location'

    # usage = fields.Selection(selection_add=[('estate', 'Estate Location')]) # fixme cannot create new record (edit oke)
    estate_location = fields.Boolean(string="Estate Location")
    estate_location_level = fields.Selection([('1','Estate'),('2','Division'),('3','Block'),('4','Sub Block')], string="Estate Location Level")
    estate_location_type = fields.Selection([('nursery','Nursery'),('planted','Planted'),('emplacement','Emplacement')], string="Estate Location Type")
    # Nursery Location
    # estate_amount_seed = fields.Integer(string="Amount of Seed")
    # estate_nursery_stage = fields.Many ... nursery module
    # Block Location
    estate_area_planted = fields.Float(string="Planted Area")
    estate_area_unplanted = fields.Float(string="Unplanted Area")
    estate_area_emplacement = fields.Float(string="Emplacement Area")
    estate_soil_type = fields.Many2one('estate.soil_type', string="Soil Type")
    estate_soil_subtype = fields.Many2one('estate.soil_sub_type', string="Soil Sub Type")
    estate_vegetation = fields.Many2one('estate.vegetation', string="Early Vegetation")
    estate_topography = fields.Many2one('estate.topography', string="Topography Type")
    estate_slope_percentage = fields.Many2one('estate.slope', string="Slope Percentage")
    estate_shape = fields.Selection([('1', 'Regular Shape'),('2','Irregular Shape')], string="Block Shape")
    estate_row_direction = fields.Many2one('estate.row_direction', string="Row Direction")
    estate_leaf_analysis = fields.Boolean(string="Leaf Analysis")
    estate_closing_block = fields.Boolean(string="Closing Block")
    estate_date_closing = fields.Date(string="Date Closing")
    estate_amount_plant = fields.Integer(string="Amount of Planted Tree")
    estate_amount_sph = fields.Integer(string="Stand per Hectare")


class SoilType(models.Model):
    _name = 'estate.soil_type'

    name = fields.Char(string="Soil Type")
    sequence = fields.Integer(string="Sequence Number")

class SoilSubtype(models.Model):
    _name = 'estate.soil_sub_type'

    name = fields.Char(string="Soil Sub Type")
    sequence = fields.Integer(string="Sequence Number")

class Vegetation(models.Model):
    _name = 'estate.vegetation'

    name = fields.Char(string="Vegetation")

class Topography(models.Model):
    _name = 'estate.topography'

    name = fields.Char(string="Topography")

class Slope(models.Model):
    _name = 'estate.slope'

    name = fields.Char(string="Slope")
    percentage_start = fields.Float(string="Start Percentage", digits=(4,2))
    percentage_end = fields.Float(string="Start Percentage", digits=(4,2))
    sequence = fields.Integer(string="Sequence Number")

class Shape(models.Model):
    _name = 'estate.shape'

    name = fields.Char(string="Block Shape")
    sequence = fields.Integer(string="Sequence Number")

class RowDirection(models.Model):
    _name = 'estate.row_direction'

    name = fields.Char(string="Row Direction")
    sequence = fields.Integer(string="Sequence Number")

class ActivityCategory(models.Model):
    _name = 'estate.activity.category'
    _parent_store = True
    _parent_name = 'parent_id'
    _order = 'sequence'
    _rec_name = 'complete_name' # alternate display record name

    name = fields.Char("Category Name", required=True,
                       help="Group of activities which has same characteristics")
    complete_name = fields.Char("Complete Name", compute="_complete_name", store=True)
    code = fields.Char("Category Code")
    type = fields.Selection([('view', "View"),
                             ('normal', "Normal")], "Type",
                            required=True,
                            help="Normal category contains activities.")
    activity_income_categ_id = fields.Many2one('account.account', "Income Account",
                                         help="This account will be used for invoices to value sales.")
    activity_expense_categ_id = fields.Many2one('account.account', "Expense Account",
                                         help="This account will be used for invoices to value expenses")
    comment = fields.Text("Additional Information")
    sequence = fields.Integer("Sequence", help="Keep category in order as plantation stages.") # todo set as parent_left at create
    parent_id = fields.Many2one('estate.activity.category', "Parent Category", ondelete='restrict')
    parent_left = fields.Integer("Parent Left",	index=True)
    parent_right = fields.Integer("Parent Right", index=True)
    child_ids = fields.One2many('estate.activity.category', 'parent_id', "Child Category")
    activity_ids = fields.One2many('estate.activity', 'activity_category_id', "Activity")

    @api.one
    @api.depends('name', 'parent_id')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        if self.parent_id:
            self.complete_name = self.parent_id.complete_name + ' / ' + self.name
        else:
            self.complete_name = self.name

        return True

class Activity(models.Model):
    _name = 'estate.activity'

    name = fields.Char("Activity Name", required=True)
    code = fields.Char("Activity Code")
    sequence = fields.Integer("Sequence", help="Keep activity in order.") # todo set as parent_left at create
    activity_category_id = fields.Many2one('estate.activity.category', "Activity Category",
                                           required=True, domain="[('type', '=', 'normal')]") # todo add domain type=normal
    activity_income_id = fields.Many2one('account.account', "Income Account",
                                         help="This account will be used for invoices to value sales.")
    activity_expense_id = fields.Many2one('account.account', "Expense Account",
                                         help="This account will be used for invoices to value expenses")

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.get('search_default_filter_category'):
            args.append((('activity_category_id', 'child_of', context['search_default_filter_category'])))
        print context;
        return super(Activity, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)

