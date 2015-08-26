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