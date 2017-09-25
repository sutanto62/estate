# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

class Activity(models.Model):
    """ Estate allocation and receivable account move required to report quantity.
    Reference and smaller using factor. Bigger reference using factor_inv.

    Example Calculation:
    Activity A, has reference, factor = 1.0 (i.e meter)
    Activity B, has bigger, factor_inv = 1000.0 (i.e kilometer)
    Activity C, has smaller, factor = 100.0 (i.e centimeter)

    Activity A quantity = 100, conversion quantity = 100/1.0
    Activity B quantity = 2, conversion quantity = 2 * 1000.0
    Activity C quantity = 200, conversion quantity = 200/100.0
    """

    _inherit = 'estate.activity'

    is_productivity = fields.Boolean('Count as Productivity', default=False,
                                     help="Define general account to enable this option.",
                                     track_visibility='onchange')
    productivity = fields.Selection([('bigger', 'Bigger than reference.'),
                                     ('reference', 'Reference productivity.'),
                                     ('smaller', 'Smaller than reference.')], 'Productivity Reference',
                                    track_visibility='onchange')
    productivity_uom_id = fields.Many2one('product.uom', string="Productivity Unit of Measurements",
                                          track_visibility='onchange')
    rounding = fields.Float('Rounding Precision', digits=0, default=0.01,
                            help="The computed quantity will be a multiple of this value. "
                                 "Use 1.0 for a Unit of Measure that cannot be further split, such as a piece.",
                            track_visibility='onchange')
    factor = fields.Float('Ratio', digits=0, default=1.0,
                          help='How much bigger or smaller this unit is compared to the reference activity: 1 * (reference unit) = ratio * (this unit)',
                          track_visibility='onchange')
    factor_inv = fields.Float('Bigger Ratio', digits=0, compute='_compute_factor_inv', readonly=True)

    @api.onchange('productivity')
    def _onchange_productivity(self):
        if self.productivity == 'reference':
            self.factor = 1

    # deprecated - a general account might have activities with different uom - use reference/bigger/smaller
    # @api.multi
    # @api.constrains('productivity_uom_id')
    # def _check_productivity_uom_id(self):
    #     """ productivity within single account should have single uom"""
    #     for record in self:
    #         uom_ids = []
    #         activity_ids = record.general_account_id and self.env['estate.activity'].search([('general_account_id', '=', record.general_account_id.id),
    #                                                                                    ('is_productivity', '=', True)]) or []
    #
    #         for activity in activity_ids:
    #             # use id instead of name to make sure single record for uom
    #             if activity.productivity_uom_id: uom_ids.append(activity.productivity_uom_id.id)
    #
    #         # warning if there is multiple uom
    #         if len(set(uom_ids)) > 1:
    #             err_msg = _('There are more than single productivity unit of measurement.\n' \
    #                         'Fix some activities in general account %s to use single productivity unit of measurement.'
    #                         % record.general_account_id.name)
    #             raise ValidationError(err_msg)
    #
    #         return uom_ids

    @api.one
    @api.depends('factor')
    def _compute_factor_inv(self):
        # set factor_inv if factor value is true, else 0.0
        self.factor_inv = self.factor and (1.0 / self.factor) or 0.0

    def convert_quantity(self, quantity):
        """
        Convert quantity to reference unit
        :param quantity:
        :param activity: estate activity ID
        :return: converted quantity
        :rtype
        """
        res = 0.0

        if type(quantity) not in (int, float):
            return 0.0

        if quantity and self.is_productivity:
            if self.productivity in ('reference', 'smaller'):
                res = quantity / self.factor
            else:
                res = quantity * self.factor_inv

        return res if res >= 0 else 0.0
