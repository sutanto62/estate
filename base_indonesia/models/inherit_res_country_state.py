from openerp import models, fields, api, exceptions

class InheritResCountryState(models.Model):

    _inherit = 'res.country.state'

    state_type = fields.Selection([
        ('city', 'City'),
        ('island', 'Island'),
        ('province', 'Province'),
    ])
    island_id = fields.Many2one('res.country.state',
                             domain="[('state_type', 'like', 'island')]")
    province_id = fields.Many2one('res.country.state',
                             domain="[('state_type', 'like', 'province')]")

