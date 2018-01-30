from openerp import models, fields, api, exceptions

class InheritResCountryState(models.Model):

    _inherit = 'res.country.state'

    state_type = fields.Selection([
        ('city', 'City'),
        ('island', 'Island'),
        ('province', 'Province'),
    ])
    island_id = fields.Many2one('res.country.state',
                             domain="[('state_type', '=', 'island')]")
    province_id = fields.Many2one('res.country.state',
                             domain="[('state_type', '=', 'province')]")


class InheritResPartnerDomain(models.Model):

    _inherit = 'res.partner'

    state_id = fields.Many2one(domain="['|', ('state_type', '=', False), \
                                        ('state_type', 'not in', ['island', 'province'])]")