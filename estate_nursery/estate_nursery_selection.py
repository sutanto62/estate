# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions

class Selection(models.Model):
    """Seed Selection"""
    _name = 'estate.nursery.selection'

    batch_id = fields.Many2one('estate.nursery.batch', "Batch")
    qty_normal = fields.Integer("Normal Seed Quantity")
    qty_abnormal = fields.Integer("Abnormal Seed Quantity")
    qty_batch = fields.Integer("DO Quantity")
    date = fields.Date("Selection Date")
    comment = fields.Text("Additional Information")
    selection_line_ids = fields.One2many('estate.nursery.selection_line', 'selection_id', "Selection Lines")

class SelectionLine(models.Model):
    """Seed Selection Line"""
    _name = 'estate.nursery.selection_line'

    qty = fields.Integer("Quantity")
    cause_id = fields.Many2one('estate.nursery.cause', "Cause")
    comment = fields.Text("Additional Information")
    selection_id = fields.Many2one('estate.nursery.selection', "Selection")

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
