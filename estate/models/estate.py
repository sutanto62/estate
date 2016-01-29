# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv

class EstateLocation(models.Model):
    """Extend Location. Have relation one-to-one with EstateBlockTemplate."""
    _inherit = 'stock.location'

    estate_location = fields.Boolean(string="Estate Location")
    estate_location_level = fields.Selection([('1','Estate'), ('2', 'Division'), ('3', 'Block'), ('4', 'Sub Block')],
                                             string="Estate Location Level")
    estate_location_type = fields.Selection([('nursery','Nursery'), ('planted', 'Planted'), ('emplacement', 'Emplacement')],
                                            string="Estate Location Type",
                                            help="Nursery: location for nursery. "
                                            "Planted: location for planting. "
                                            "Emplacement: location for non-planting/nursery.")

    # @deprecated - move to Estate Block
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
        return super(Activity, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)

class LabourType(models.Model):
    _name = 'estate.labour.type'

    name = fields.Char('Name')

class EstateObject(models.Model):
    """Group of upkeep object
    Problem:
    * Single activity entry to a group of objects. i.e: fertilizing NPK to a group of blocks.
    * Object types are locations, buildings, infrastructures.
    """
    _name = 'estate.object'

    name = fields.Char("Name")
    #object_type_id = fields.Many2one('estate.object.type', "Type")
    #object_line_ids = fields.One2many('estate.object.line', 'object_id')

class EstateObjectType(models.Model):
    """Type of group
    """
    _name = 'estate.object.type'

    name = fields.Char("Name")

class EstateBlockTemplate(models.Model):
    """Block is a unit of an Estate. Hierarchical as Estate, Division, Block or Sub Block.
    Block is delegation inheritance of Stock Location.
    """

    _name = 'estate.block.template'
    _inherits = {'stock.location': 'inherit_location_id'}

    inherit_location_id = fields.Many2one('stock.location', required=True, ondelete="restrict")
    batch_id = fields.Many2one('estate.nursery.batch', "Seed Source")
    area_gis = fields.Float("GIS Area (ha)", (18, 6), help="Closing block area.")
    area_planted = fields.Float("Planted Area (ha)", (18, 6),
                                help="Calculated based on stand per hectare.")
    area_emplacement = fields.Float("Emplacement Area (ha)",
                                    help="Area for office and housing.")
    area_unplanted = fields.Float("Unplanted Area (ha)",
                                  help="GIS Area minus Planted area.")

    is_smallholder = fields.Boolean("Smallholder Area",
                             help="Check this box to mark Block as Smallholder area.")
    partner_id = fields.Many2one('res.partner', "Owner", domain="[('is_company', '=', 'true')]",
                                 help="Define child elements owner if childs has no owner. "
                                 "Child able to overide parent's owner partner.")
    leaf_analysis = fields.Boolean("Leaf Analysis", help="Set true if leaf analysis has been done.")
    soil_analysis = fields.Boolean("Soil Analysis", help="Set true if soil analysis has been done.")
    date_planted = fields.Date("Planted Date")
    qty_tree = fields.Integer("Total Tree")
    qty_tree_immature = fields.Integer("Immature Tree")
    qty_tree_mature_normal = fields.Integer("Normal Mature Tree")
    qty_tree_mature_abnormal = fields.Integer("Abnormal Mature Tree")
    qty_tree_mature_nofruit = fields.Integer("Tree Without Fruit")
    planted_year_id = fields.Many2one('estate.planted.year', "Planted Year") # Hide if estate_location_level in ('1', '2')
    block_ids = fields.One2many('estate.block', 'block_template_id', "Block Variants")
    block_parameter_ids = fields.One2many('estate.block.parameter', 'block_id', "Block Parameter",
                                          help="Define block parameter")

    # Set default value embedded object (stock location)
    _defaults = {
        'estate_location': 'true',
        'estate_location_type': 'planted'
    }

class EstateBlock(models.Model):
    _name = 'estate.block'
    _inherits = {'estate.block.template': 'block_template_id'}

    block_template_id = fields.Many2one('estate.block.template', "Block Template")
    parameter_value_ids = fields.Many2many('estate.parameter.value', id1='block_id', id2='val_id', string="Parameter Value")

class BlockParameter(models.Model):
    """Parameter of Block.
    """
    _name = 'estate.block.parameter'
    #_rec_name = 'parameter_id'

    block_id = fields.Many2one('estate.block.template', "Estate Block")
    parameter_id = fields.Many2one('estate.parameter', "Parameter", ondelete='restrict')
    parameter_value_id = fields.Many2one('estate.parameter.value', "Value",
                                         domain="[('parameter_id', '=', parameter_id)]",
                                         ondelete='restrict')
    # value_ids = fields.Many2many('estate.parameter.value', id1='line_id', id2='val_id', string="Estate Parameter Value")

class Parameter(models.Model):
    """Parameter for Block (exclude Planted Year).
    """
    _name = 'estate.parameter'

    name = fields.Char("Parameter Name")
    mandatory = fields.Boolean("Mandatory", help="Checking this option to make it as mandatory Block Parameter.")
    level = fields.Selection([('1', 'Estate'), ('2', 'Division'), ('3', 'Block'), ('4', 'Sub Block')],
                             string="Parameter Level",
                             help="Define block level parameter.")

class ParameterValue(models.Model):
    """Selection value for Parameter.
    """
    _name = 'estate.parameter.value'

    name = fields.Char('Value', translate=True, required=True)
    parameter_id = fields.Many2one('estate.parameter', "Parameter", ondelete='restrict')
    # block_ids = fields.Many2many('estate.block', id1='val_id', id2='block_id', string="Block")


class PlantedYear(models.Model):
    """@deprecated: change to product variants.
    """
    _name = 'estate.planted.year'

    name = fields.Char("Planted Year")