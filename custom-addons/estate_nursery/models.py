# -*- coding: utf-8 -*-

from openerp import models, fields, api

# class estate_nursery(models.Model):
#     _name = 'estate_nursery.estate_nursery'

#     name = fields.Char()

class SeedVariety(models.Model):
    _name = 'estate_nursery.seed_variety'

    name = fields.Char(string="Variety Name")
    code = fields.Char(string="Variety Short Name")
    description = fields.Text()
    partner_id = fields.Many2one('res.partner', string="Supplier", domain=[('supplier','=',True)])

class SeedProgeny(models.Model):
    _name = 'estate_nursery.seed_progeny'

    name = fields.Char(string="Progeny Name")
    code = fields.Char(string="Progeny Short Name")
    description = fields.Text()

class NurseryBlock(models.Model):
    # Inherit Location object to be Nursery Block
    _name = 'estate_nursery.block'
    _inherit = 'stock.location'
    _parent_store = True
    _parent_name = 'location_id'
    _parent_order = 'name'
    _order = 'parent_left'

    def _name_get(self, cr, uid, location, context=None):
        name = location.name
        while location.location_id and location.usage != 'view':
            location = location.location_id
            name = location.name + '/' + name
        return name

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for location in self.browse(cr, uid, ids, context=context):
            res.append((location.id, self._name_get(cr, uid, location, context=context)))
        return res

    location_id = fields.Many2one('estate_nursery.block', select=True, string="Parent Location", ondelete='set null')
    child_ids = fields.One2many('estate_nursery.block', 'location_id', string="Child")
    parent_left = fields.Integer('Parent Left', index=True)
    parent_right = fields.Integer('Parent Right', index=True)
