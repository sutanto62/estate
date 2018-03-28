# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError, AccessError
import openerp.addons.decimal_precision as dp


class MaterialOrder(models.Model):
    """ Wrapper of stock picking. Create one or more stock picking by destination location.

        Material order is a wrapper for estate assistant/stock officer request/return stock material
        from a warehouse. Material line could consists of any material requirement for any location.
        User should have access stock/estate user in order to input request/return order.

        Approved status will create one or many stock picking for each location.
        Done status indicate all stock picking has been done.

    """
    _name = 'estate_stock.material_order'
    _description = 'Material Order'
    _inherit = ['mail.thread']

    name = fields.Char('Material Order No')
    employee_id = fields.Many2one('hr.employee', 'Requestor')
    estate_id = fields.Many2one('estate.block.template', 'Estate', domain="[('estate_location_level', '=', '1')]")
    estate_location_id = fields.Many2one('stock.location', 'Estate Location', readonly=True,
                                         related='estate_id.inherit_location_id')
    division_id = fields.Many2one('estate.block.template', 'Division',
                                  domain="[('inherit_location_id', 'child_of', estate_location_id), ('estate_location_level', '=', '2')]")
    division_location_id = fields.Many2one('stock.location', 'Division Location', readonly=True,
                                           related='division_id.inherit_location_id')
    date_expected = fields.Date('Date Expected', track_visibility="onchange", required=True)
    material_ids = fields.One2many('estate_stock.material_line', 'order_id', string='Material Line',
                                   readonly=True,
                                   states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    move_type = fields.Selection([('direct', 'Partial'), ('one', 'All at once')], 'Delivery Method', required=True,
                                 track_visibility='onchange',
                                 default='direct', help="It specifies goods to be deliver partially or all at once")
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', track_visibility="onchange",
                                      required=True)
    company_id = fields.Many2one('res.company', related='picking_type_id.warehouse_id.company_id',
                                           store=True, readonly=True)
    origin = fields.Char('Source Document', track_visibility="onchange")
    stock_picking_amount = fields.Integer('Stock Picking', compute='_compute_stock_picking')
    stock_move_amount = fields.Integer('Stock Move', compute='_compute_stock_move')
    stock_move_available = fields.Integer('Available Stock Move', compute='_compute_stock_available')
    stock_move_done = fields.Integer('Transfered Stock Move', compute='_compute_stock_done')
    # picking_type_code = fields.related('picking_type_id', 'code', type='selection', selection=[('incoming', 'Suppliers'), ('outgoing', 'Customers'), ('internal', 'Internal')]),
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('approve', 'Approved'),
                              ('waiting', 'Waiting Another Operation'),
                              ('partially_available', 'Partially Available'),
                              ('cancel', 'Cancel'),
                              ('done', 'Done')],
                             default='draft', string='Status', track_visibility='onchange', readonly=True)
    readonly = fields.Boolean('Readonly', default=False, compute='_compute_readonly')
    type = fields.Selection([('general', 'General Material'),
                             ('estate', 'Estate Material')], required=True,
                             default='general', string='Material Order Type', track_visibility='onchange',
                             help="Define cost center.")

    # state_update = fields.Integer('Dummy', compute='_compute_state')

    @api.multi
    def _compute_stock_picking(self):
        """ Display how many stock picking created."""
        self.ensure_one()
        res = len(self.stock_pickings(state=['draft', 'waiting', 'confirmed', 'partially_available', 'assigned', 'done']))
        self.stock_picking_amount = res
        return res

    @api.multi
    def _compute_stock_move(self):
        """ Display how many stock moves already available."""
        self.ensure_one()
        res = len(self.stock_moves(state=['draft', 'waiting', 'confirmed', 'partially_available', 'assigned', 'done']))
        self.stock_move_amount = res
        return res

    @api.multi
    def _compute_stock_available(self):
        """ Stock officer has marked picking as to do."""
        self.ensure_one()
        res = len(self.stock_moves(state=['assigned']))
        self.stock_move_available = res
        return res

    @api.multi
    def _compute_stock_done(self):
        """ Stock officer has validated picking."""
        self.ensure_one()
        res = len(self.stock_moves(state=['done']))
        self.stock_move_done = res
        return res

    @api.multi
    def _compute_readonly(self):
        """ Help set readonly attribute at field xml.

        Readonly            | Draft     | Confirmed | Approved  | Done
        Inventory User      | False     | True      | True      | True
        Inventory Asstant   | False     | True      | True      | True
        Inventory Manager   | False     | False     | True      | True
        """

        for record in self:
            state = record.state not in ('draft', 'confirm')
            state_manager = record.state in ('confirm', 'approve') and not self.user_has_groups(
                'stock.group_stock_manager')
            record.readonly = state or state_manager

    @api.model
    def create(self, vals):
        if vals['picking_type_id']:
            picking_type_id = self.env['stock.picking.type'].browse(vals['picking_type_id'])

            if not picking_type_id.mo_sequence_id:
                err_msg = _(
                    'No material order sequence for %s found. Please contact your Administrator.' % picking_type_id.complete_name)
                raise ValidationError(err_msg)

            sequence_id = self.env['ir.sequence'].browse(picking_type_id.mo_sequence_id.id)
            res = sequence_id.next_by_id()
            vals['name'] = res
        return super(MaterialOrder, self).create(vals)

    @api.multi
    def unlink(self):
        """ Do not delete material order unless draft. Keep it simple with delete condition."""
        for record in self:
            if not record.state == 'draft':
                err_msg = _('Only draft material order could be deleted.')
                raise ValidationError(err_msg)
            super(MaterialOrder, record).unlink()

        return True

    @api.multi
    def action_draft(self):
        """ Set material order to draft as long as picking and its stock move is draft.
            Drafting create problem:
            1. Stock inventory.
            2. Stock valuation.
        """
        # Only stock manager allow to draft
        if not self.user_has_groups('stock.group_stock_manager'):
            err_msg = _('You have no access to draft this record.')
            raise AccessError(err_msg)

        for record in self:
            # Check if there are pickings either its state in draft
            if not record.stock_pickings() or set(record.stock_pickings().mapped('state')) == set(['draft']):
                record.state = 'draft'
            else:
                err_msg = _('Some of %s stock pickings has been processed.' % record.name)
                raise ValidationError(err_msg)

    @api.multi
    def action_confirm(self):

        if not self.user_has_groups('stock.group_stock_assistant'):
            err_msg = _('You have no access to confirm this record.')
            raise AccessError(err_msg)

        # do not confirm empty material line
        for record in self:
            if not record.material_ids:
                err_msg = _('No material requested.')
                raise ValidationError(err_msg)

            record.state = 'confirm'

    @api.multi
    def action_approve(self):
        """ Process material order to warehouse."""

        # Only stock manager allowed to approve material order
        if not self.user_has_groups('stock.group_stock_manager'):
            err_msg = _('You have no access to approve this record.')
            raise AccessError(err_msg)

        for record in self:
            # do not approve empty material line.
            if not record.material_ids:
                err_msg = _('No material requested.')
                raise ValidationError(err_msg)

            record.state = 'approve'

            # Prevent double approve create multiple picking
            if not record.stock_pickings():
                record.create_picking()

    @api.multi
    def action_wait(self):
        """ Inform requestor all products are not available and waiting for another operation."""
        for record in self:
            record.state = 'waiting'

    @api.multi
    def action_partial(self):
        """ Inform requestor some products are available and waiting for another operation."""
        for record in self:
            record.state = 'partially_available'

    @api.multi
    def action_cancel(self):
        """ Cancel is a business action. Allow only when stock pickings in confirmed or assigned"""

        # Only stock manager allowed to approve material order
        if not self.user_has_groups('stock.group_stock_user'):
            err_msg = _('You have no access to cancel this record.')
            raise AccessError(err_msg)

        for record in self:
            # confirmed - approved material order created confirmed pickings.
            picking_ids = record.stock_pickings()
            if set(picking_ids.mapped('state')).issubset(['cancel', 'confirmed', 'assigned']):
                # cancel material order by cancel all picking
                for picking in picking_ids:
                    picking.action_cancel()
            else:
                err_msg = _('Some of %s stock pickings has been processed.' % record.name)
                raise ValidationError(err_msg)

    @api.multi
    def action_done(self):
        """ @deprecated use inventory workflow. Material order status follow stock picking status.
            All products have been received. Mark related picking to done."""
        if not self.user_has_groups('stock.group_stock_user'):
            err_msg = _('You have no access to receive material.')
            raise AccessError(err_msg)

        for record in self:
            record.state = 'done'

    @api.multi
    def action_view_stock_pickings(self):
        """ User need to display related stock pickings."""
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('origin', '=', self.name)]
        return action

    @api.multi
    def action_view_stock_moves(self):
        """ User need to display related stock moves."""
        self.ensure_one()
        picking_ids = self.env['stock.picking'].search([('origin', '=', self.name)])
        action = self.env.ref('stock.action_move_form2').read()[0]
        action['domain'] = [('picking_id', 'in', picking_ids.ids)]
        return action

    @api.multi
    def create_picking(self):
        """ Material order is a wrapper of stock picking. Create separate picking for different block.
            Set picking to confirmed reduce stock user administrative effort.
        """
        material_line_obj = self.env['estate_stock.material_line']

        for order in self:
            # picking data
            vals = {
                'picking_type_id': order.picking_type_id.id,
                'company_id': order.picking_type_id.warehouse_id.company_id.id,
                'location_id': order.picking_type_id.default_location_src_id.id,
                'location_dest_id': order.picking_type_id.default_location_dest_id.id,
                'move_type': order.move_type,
                'priority': '1',
                'min_date': order.date_expected,
                'origin': order.name,
                'move_lines': []
            }

            location_dest_ids = self.get_location(order)
            for location in location_dest_ids:
                vals['location_dest_id'] = location

                # use picking type sequence naming
                ptype_id = vals.get('picking_type_id', self._context.get('default_picking_type_id', False))
                sequence_id = self.env['stock.picking.type'].browse(ptype_id).sequence_id
                vals['name'] = sequence_id.next_by_id()

                # prepare stock move data
                domain = [('order_id', 'in', order.ids)]
                if order.type == 'estate':
                    domain.append(('location_id', '=', location))
                material_ids = material_line_obj.search(domain).mapped('product_id')
                move_lines = []
                
                for product in set(material_ids):
                    product_domain = domain
                    product_domain.append(('product_id', '=', product.id))
                    product_uom_qty = sum(q.product_uom_qty for q in material_line_obj.search(product_domain))
                    
                    move_val = {
                        'name': product.name,
                        'product_id': product.id,
                        'product_uom': product.uom_id.id,
                        'product_uom_qty': product_uom_qty,
                        'location_id': vals['location_id'],
                        'location_dest_id': vals['location_dest_id'],
                        'company_id': vals['company_id']
                    }
                    move_lines.append((0, 0, move_val))
                vals['move_lines'] = move_lines

                # create picking and mark to do (ready to validate)
                picking = self.env['stock.picking'].with_context({'mail_create_nosubscribe': True}).create(vals)

                picking.action_confirm()

        return True

    # @api.multi
    # def stock_pickings(self, state=[]):
    #     """ Display all created stock picking from approved material order."""
    #     # self.ensure_one() - do not use ensure_one(). error update stock quantity
    #     stock_picking_obj = self.env['stock.picking']
    #     domain = [('origin', '=', self.name)]
    #     if state:
    #         domain.append(('state', 'in', state))
    #     picking_ids = stock_picking_obj.search(domain)
    #     return picking_ids

    @api.multi
    def stock_pickings(self, state=[], origin=None):
        """
        Get stock pickings from material order.
        :param state: state of picking
        :param origin: material order name
        :return: picking recordset
        """
        # self.ensure_one() - do not use ensure_one(). error update stock quantity
        stock_picking_obj = self.env['stock.picking']

        domain = [('origin', '=', origin if origin is not None else self.name)]
        if state:
            domain.append(('state', 'in', state))
        picking_ids = stock_picking_obj.search(domain)

        return picking_ids

    @api.multi
    def stock_moves(self, state=[], origin=None):
        """
        Display all created stock move (from one or many stock picking) from approved material order.
        :param state: state of stock move
        :param origin: material order name
        :return: stock move recordsets
        """
        self.ensure_one()
        stock_move_obj = self.env['stock.move']
        picking_ids = self.stock_pickings(origin=origin)
        domain = [('picking_id', 'in', picking_ids.ids)]
        if state:
            domain.append(('state', 'in', state))
        stock_move_ids = stock_move_obj.search(domain)
        return stock_move_ids

    def get_location(self, order):
        """ picking must be in single source and destination location for traceability."""
        location_ids = []
        if order.type == 'estate':
            for line in order.material_ids:
                location_ids.append(line.location_id.id)
            return set(location_ids)
        elif order.type == 'general':
            res = self.env.ref('stock.stock_location_scrapped').id
            return [res]
        else:
            return location_ids

class MaterialOrderLine(models.Model):
    _name = 'estate_stock.material_line'
    _description = 'Material Line'

    order_id = fields.Many2one('estate_stock.material_order', 'Material Order')
    type = fields.Selection(string='Material Order Type', related='order_id.type', store=True, readonly=True)
    company_id = fields.Many2one('res.company', string="Warehouse Company", related='order_id.company_id',
                                 store=True, readonly=True, help='Required for creating journal entry.')
    estate_id = fields.Many2one('estate.block.template', 'Estate', related='order_id.estate_id',
                                store=True, readonly=True)
    division_id = fields.Many2one('estate.block.template', 'Division', related='order_id.division_id',
                                  store=True, readonly=True)
    division_location_id = fields.Many2one('stock.location', 'Division Location',
                                           related='order_id.division_location_id',
                                           readonly=True)
    product_id = fields.Many2one('product.product', 'Product',
                                 domain=[('type', '=', 'product'), ('categ_id.estate_product', '=', 'True')],
                                 required=True)
    product_uom_id = fields.Many2one('product.uom', string='Unit of Measure', related='product_id.uom_id', store=True,
                                     readonly=True, help='Usage unit of measure. Define at product.')
    product_uom_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
                                   required=True)
    block_id = fields.Many2one('estate.block.template', 'Block', help="Select estate material order type to enable",
                               domain="[('inherit_location_id', 'child_of', division_location_id), ('estate_location_level', '=', '3')]")
    partner_id = fields.Many2one('res.partner', string='Block Partner', compute='_compute_partner_id', store=True,
                                 help='Required for creating journal entry with different company.')
    location_id = fields.Many2one(related='block_id.inherit_location_id', string='Stock Location', store=True,
                                  readonly=True, help='Required for creating stock move.')
    activity_id = fields.Many2one('estate.activity', 'Activity', domain=[('type', '=', 'normal')],
                                  help='Required for creating journal entry.')
    # general_account_id = fields.Many2one('account.account', 'General Account')
    # account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    @api.multi
    @api.depends('block_id')
    def _compute_partner_id(self):
        """ Computed based on block/vehicle/machine/others"""
        for material in self:
            # partner from block
            if material.block_id:
                material.partner_id = material.block_id.company_id.partner_id.id


    @api.model
    def create(self, vals):
        """ Set stock location for general"""

        return super(MaterialOrderLine, self).create(vals)
