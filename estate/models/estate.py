# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv
# from openerp.addons.base_geoengine import geo_model
# from openerp.addons.base_geoengine import fields as geo_fields

class EstateLocation(models.Model):
    """Extend Location. Have relation one-to-one with EstateBlockTemplate."""
    _inherit = 'stock.location'

    estate_code = fields.Char('Estate Code', help='Use by Employee Identity Number')
    estate_location = fields.Boolean(string="Estate Location")
    estate_location_level = fields.Selection([('1','Estate'), ('2', 'Division'), ('3', 'Block'), ('4', 'Sub Block')],
                                             string="Estate Location Level")
    estate_location_type = fields.Selection([('nursery','Nursery'), ('planted', 'Planted'), ('emplacement', 'Emplacement')],
                                            string="Estate Location Type",
                                            help="Nursery: location for nursery. \n"\
                                            "Planted: location for planting. \n"\
                                            "Emplacement: location for non-planting/nursery.")

    def get_estate(self, id):
        """
        Get estate of a location
        :param id: a location
        :return: estate location
        """
        parent = self.env['stock.location'].search([('id', '=', id)]).location_id
        if parent.estate_location_level == '1':
            return parent
        else:
            return self.get_estate(parent.id)

    def get_division(self, id):
        """
        Get division of a location
        :param id: a location
        :return: division location
        """
        parent = self.env['stock.location'].search([('id', '=', id)], limit=1).location_id
        level = parent.estate_location_level

        if not parent:
            return

        if level == '2':
            return parent
        elif level in ['3', '4']:
            return self.get_division(parent.id)
        else:
            # If have new estate level location
            return


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
    _inherit = 'mail.thread'

    inherit_location_id = fields.Many2one('stock.location', required=True, ondelete="restrict")
    assistant_id = fields.Many2one('hr.employee', "Assistant", ondelete="restrict")
    # batch_id = fields.Many2one('estate.nursery.batch', "Seed Source", required=False, ondelete="restrict",
    #                            help='Use batch for nursery block only.')
    area_gis = fields.Float("GIS Area (ha)", digits=(18, 6), help="Area registered at Izin Lokasi - based on GIS.")
    area_planted = fields.Float("Planted Area (ha)", digits=(18, 6), track_visibility='onchange',
                                help="Area which has been planted excluded infrastructure and emplacement.")
    area_infrastructure = fields.Float("Infrastructure Area (ha)", digits=(18, 6),
                                    help="Area for road.")
    area_emplacement = fields.Float("Emplacement Area (ha)", digits=(18, 6),
                                    help="Area for office and housing.")
    area_unplanted = fields.Float("Unplanted Area (ha)", digits=(18, 6),
                                  help="Area which could be planted or not yet planted excluded infrastructure and"
                                       "emplacement")
    area_non_company = fields.Float("Non GRTT (ha)",  digits=(18, 6),
                                    help="Area which not belong to company but included in Izin Lokasi.")
    qty_sph_standard = fields.Integer(compute="_get_stand_hectare", string="Standard stand per hectare",
                                      store=True, help="Average stand per hectare by topography.")
    qty_sph_do = fields.Integer(compute="_get_stand_hectare", string="Stand per hectare",
                                store=True, help="Average stand per hectare planted.")
    is_smallholder = fields.Boolean("Smallholder Area",
                             help="Check this box to mark Block as Smallholder area.")
    company_id = fields.Many2one('res.company', "Company", track_visibility='onchange',
                                 help="Based on Consession License.")
    leaf_analysis = fields.Boolean("Leaf Analysis", help="Set true if leaf analysis has been done.")
    soil_analysis = fields.Boolean("Soil Analysis", help="Set true if soil analysis has been done.")
    date_planted = fields.Date("Planted Date")
    qty_tree = fields.Integer("Total Tree", track_visibility='onchange')
    qty_tree_immature = fields.Integer("Immature Tree")
    qty_tree_mature_normal = fields.Integer("Normal Mature Tree")
    qty_tree_mature_abnormal = fields.Integer("Abnormal Mature Tree")
    qty_tree_mature_nofruit = fields.Integer("Tree Without Fruit")
    planted_year_id = fields.Many2one('estate.planted.year', "Planted Year", track_visibility='onchange') # Hide if estate_location_level in ('1', '2')
    block_ids = fields.One2many('estate.block', 'block_template_id', "Block Variants")
    block_parameter_ids = fields.One2many('estate.block.parameter', 'block_id', "Block Parameter",
                                          help="Define block parameter")
    closing = fields.Boolean("Closing Block", help="Standard work result applied.")
    account_id = fields.Many2one('account.analytic.account', 'Analytic Account', track_visibility='onchange',
                                 domain=[('use_estate', '=', True), ('account_type', '=', 'normal')], help="Analytic Account by Batch/Year Planted")

    # Set default value embedded object (stock location)
    _defaults = {
        'estate_location': 'true',
        'estate_location_type': 'planted',
        'usage': 'internal'
    }

    @api.one
    @api.depends('block_parameter_ids', 'qty_tree')
    def _get_stand_hectare(self):
        if self.block_parameter_ids:
            # Set as based on topography parameter value
            self.qty_sph_standard = 126
        else:
            # Set default (based on stand per hectare default value)
            self.qty_sph_standard = 130

class EstateBlock(models.Model):
    _name = 'estate.block'
    _inherits = {'estate.block.template': 'block_template_id'}

    block_template_id = fields.Many2one('estate.block.template', "Block Template", required=True, ondelete="restrict")
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
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account ')
    active = fields.Boolean('Active', default=True)

class StandPerHectare(models.Model):
    """Stand per hectare by regional. Parameter value constrains to topography parameter (hard coded).
    """
    _name = 'estate.stand.hectare'

    name = fields.Char("Name")
    qty = fields.Integer("Stand Per Hectare")
    default = fields.Boolean("Set as default for new Block", help="Set True to make new block using this stand per hectare.")
    parameter_value_id = fields.Many2one('estate.parameter.value', "Topography",
                                         domain="[('parameter_id.id', '=', 'estate.parameter_topography')]")

    @api.onchange('default')
    def _onchange_default(self):
        """Only one default stand per hectare allowed.
        """
        records = self.env['estate.stand.hectare'].search([('id', '!=', self.id)])
        for rec in records:
            rec.default = 'False'

