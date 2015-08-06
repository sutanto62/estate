# -*- coding: utf-8 -*-

from openerp import models, fields, api

class EstateBlock(models.Model):
    """Extend Location"""
    _name = 'estate.estate_block'
    _inherit = 'stock.location'

    block_type_id = fields.Many2one('estate.block_type', string="Block Type")

class BlockType(models.Model):
    """Determine cost center level. Estate > Division > Block"""
    _name = 'estate.block_type'

    name = fields.Char(string='Block Type Name');

class EstateLocation(models.Model):
    """Extend Location for Estate Location (Estate, Division, Block)"""
    _inherit = 'stock.location'

    usage = fields.Selection(selection_add=[('estate', 'Estate Location')])
    estate_location_level = fields.Selection([('1','Estate'),('2','Division'),('3','Block'),('4','Sub Block')], string="Estate Location Level")