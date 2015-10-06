# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions

# class SelectionReceiveWizard(models.TransientModel):
#     """
#     Selection Wizard for seed receiving
#     """
#     _name = 'estate.nursery.selection_receive_wizard'
#
#     selection_ids = fields.Many2many('estate.nursery.selection_receive_line', "Bags")
#
# class SelectionReceiveLine(models.Model):
#     """
#     Inherits batchline
#     """
#     _name = 'estate.nursery.selection_receive_line'
#
#     batchline_id = fields.Many2one('estate.nursery.batchline', "Bag")
#     qty_received = fields.Integer("Quantity Received", related='batchline_id.seed_qty', help="Fill in with written packaging quantity.")
#     qty_single = fields.Integer("Single", help="Write single tone seed.")
#     qty_double = fields.Integer("Double", help="No triple/quartet allowed.")
#     qty_broken = fields.Integer("Broken", help="Cause by transportation.")
#     qty_dead = fields.Integer("Dead", help="Not alive.")
#     qty_fungus = fields.Integer("Fungus", help="Seed with fungus.")
#     sub_total_normal = fields.Integer("Total Accepted", compute='_compute_total_normal')
#     sub_total_reject = fields.Integer("Total Rejected", compute='_compute_total_reject')
#     ratio_normal = fields.Float("% Normal", digits="2,2", compute='_compute_ratio(sub_total_reject, qty_received)')
#
#     @api.one
#     @api.depends('qty_single', 'qty_double')
#     def _compute_total_normal(self):
#         self.sub_total_normal = self.qty_single + self.qty_double
#
#     @api.one
#     @api.depends('qty_broken', 'qty_dead', 'qty_fungus')
#     def _compute_total_reject(self):
#         self.sub_total_reject = self.qty_broken + self.qty_dead + self.qty_fungus
#
#     @api.one
#     @api.depends('sub_total_normal', 'sub_total_reject')
#     def _compute_ratio(self, a, b):
#         self.ratio_normal = float(a)/float(b)