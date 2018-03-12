# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _

class SlaVendorManagement(models.Model):
    _name = 'sla.vendor.management'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name', required=True)
    days = fields.Integer(string='Days', required=True)
    count_weekend = fields.Boolean(string='Include Weekend')

    @api.multi
    @api.constrains('code')
    def _check_available_code(self):
        # Check if new code does not conflicted with existing
        sla_id = self.get_available_code(self.id, self.code)
        if sla_id:
            raise exceptions.ValidationError('Current code is exist, please use another code!')

    def get_available_code(self, id, code):
        # Search record with same code but different id
        sla_id = self.env['sla.vendor.management'].search([('id', '!=', id),('code', '=', code)])
        return sla_id