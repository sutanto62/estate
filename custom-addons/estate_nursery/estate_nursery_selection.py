# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions

class Selection(models.Model):
    """Delegation Inheritance Stock Quant for Seed Selection"""
    _name = 'estate.nursery.selection'
    _inherits = {'stock.quant': 'quant_id'}

    #quant_id = fields.Many2one('stock.quant') #bag
    bag_selection_ids = fields.One2many('estate.nursery.selection_line','selection_id',"Selection")


class SelectionLine(models.Model):
    """Quantity and condition of Seed Selection per Bag"""
    _name = 'estate.nursery.selection_line'

    selection_id = fields.Many2one('estate.nursery.selection',"Selection")
    qty = fields.Integer('Quantity')
    cause_id = fields.Many2one('estate.nursery.cause', "Cause")

class Cause(models.Model):
    """Selection Cause (normal, afkir, etc)."""
    _name = 'estate.nursery.cause'
    _sequence = 'sequence'

    name = fields.Char('Name')
    comment = fields.Text('Cause Description')
    code = fields.Char('Cause Abbreviation', size=3)
    sequence = fields.Integer('Sequence No')
    selection_type = fields.Selection([('0', 'Broken'),('1', 'Normal'),('2', 'Politonne')], "Selection Type")
    stage_id = fields.Many2one('estate.nursery.stage', "Nursery Stage")