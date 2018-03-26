# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError, UserError, Warning


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    estate_id = fields.Many2one('estate.block.template', 'Estate')
    division_id = fields.Many2one('estate.block.template', 'Division')
    division_location_id = fields.Many2one('stock.location', 'Division Location', related='division_id.inherit_location_id')
    date_expected = fields.Date('Date Expected')
    state = fields.Selection(selection_add=[('validated', 'Validated'),
                                            ('approved', 'Approved'),
                                            ('ordered', 'Ordered')])
    multi_location = fields.Boolean('Multi Location', default=False,
                                      help="Set multi location in order to deliver product at several location.")

    @api.onchange('division_id')
    def _onchange_division_id(self):
        """ Company defined by division."""

        if self.division_id:
            self.company_id = self.division_id.company_id.id

    @api.multi
    def action_confirm(self):
        """ Material order should be approved before picking marked as todo"""

        material_id = self.env['estate_stock.material_order'].search([('name', '=', self.origin)])
        if material_id and material_id.state != 'approve':
            err_msg = _('Stock picking could not marked to do as material order not approved yet.')
            raise ValidationError(err_msg)

        return super(StockPicking, self).action_confirm()

        # Display warning
        self.move_lines

    @api.multi
    def action_assign(self):
        """ Notify user unable to reserve."""
        res = super(StockPicking, self).action_assign()
        if self.move_type == 'one' and set(['confirmed']).issubset(set(self.move_lines.mapped('state'))):
            err_msg = _('Unable to reserve. Some of your required product is waiting for availability.')
            raise ValidationError(err_msg)
        return res

    # Backordered stock picking might be canceled for operation reason.
    # @api.multi
    # def action_cancel(self):
    #     """ Cancel stock picking of an material order should be rejected."""
    #     for record in self:
    #         if record.origin and self.env['estate_stock.material_order'].search([('name', '=', record.origin)]):
    #             err_msg = _('Do not cancel stock picking which has material order.')
    #             raise ValidationError(err_msg)
    #         super(StockPicking, record).action_cancel()
    #
    #     return True


class StockMove(models.Model):
    """ Inherit estate, division"""

    _inherit = 'stock.move'

    estate_id = fields.Many2one(related='picking_id.estate_id', store=True, readonly=True)
    division_id = fields.Many2one(related='picking_id.division_id', store=True, readonly=True)

    @api.multi
    def action_done(self):
        """ Make sure material order state updated as all stock move done (validate)."""

        for record in self:
            super(StockMove, record).action_done()

            # Update material order if all stock moves has been done
            material_order_id = record.get_material_order()
            if len(material_order_id) > 0:
                picking_ids = material_order_id.stock_pickings()
                if set(picking_ids.mapped('state')) == set(['done']):
                    material_order_id.state = 'done'

    @api.multi
    def action_cancel(self):
        """ Update material order to done if there's no stock pickings left (done or cancel)."""
        for record in self:
            super(StockMove, record).action_cancel()

            # Update material order status if all stock move cancel
            material_order_id = record.get_material_order()
            if len(material_order_id) > 0:
                res = material_order_id.stock_pickings().mapped('state')
                if set(res).issubset(['cancel']):
                    material_order_id.state = 'cancel'

    # do not override action_assign, prevent backorder created.
    # @api.multi
    # def action_assign(self):
    #     """ Odoo did not show warning of empty stock."""
    #     product_empty = []
    #     for move in self:
    #         super(StockMove, move).action_assign()
    #         if move.state == 'confirmed':
    #             product_empty.append(move.product_id.name)
    #
    #     if product_empty:
    #         raise ValidationError(_('%s has no stock.' % ', '.join(set(product_empty))))

    @api.model
    def get_material_order(self):
        """ Allow to find material order of a single stock move."""
        res = self.env['estate_stock.material_order'].search([('name', '=', self.picking_id.origin)])
        return res


class PickingType(models.Model):
    """ Material order maintain different sequence."""

    _inherit = "stock.picking.type"

    mo_sequence_id = fields.Many2one('ir.sequence', 'Material Order Sequence', help='Warehouse need to maintain material request')

