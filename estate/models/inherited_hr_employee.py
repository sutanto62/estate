# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class Employee(models.Model):
    """Extend HR Employee.
    """
    _inherit = 'hr.employee'

    estate_id = fields.Many2one('estate.block.template', 'Estate', help='Help to define NIK for estate labour',
                                domain=[('estate_location', '=', True), ('estate_location_level', '=', '1')])

    @api.multi
    def generate_nik(self, vals):
        """ Extend Employee._generate_nik on hr_employee module
        ir_sequence_code_1 = PKWTT/PKWT Monthly/PKWT Daily
        ir_sequence_code_2 = Estate
        """

        if vals.get('contract_type') == '2' and vals.get('contract_period') == '2' \
                and vals.get('company_id') and vals.get('estate_id'):
            seq_obj = self.env['ir.sequence']
            # estate = {'LYD': '1'}  # Key is block template name, Value is number as memo internal.
            estate_id = self.env['estate.block.template'].search([('id', '=', vals.get('estate_id'))], limit=1)
            company_id = self.env['res.company'].search([('id', '=', vals.get('company_id'))])
            prefix = '%(' + estate_id.name + ')s'

            # Use 0 if no code find
            if hasattr(self.env['stock.location'], 'estate_code') or estate_id.estate_code:
                map_estate = {estate_id.name: estate_id.estate_code}
                d = prefix % map_estate
            else:
                d = prefix % '0'

            # Use 00 if no code find
            if hasattr(self.env['res.company'], 'code'):
                sequence_code = 'hr_indonesia.' + '3' + company_id.code + d
            else:
                sequence_code = 'hr_indonesia.' + '3XXX' + d

            res = seq_obj.next_by_code(sequence_code)
            return res
        else:
            return super(Employee, self).generate_nik(vals)

