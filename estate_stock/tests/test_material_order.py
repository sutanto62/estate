# -*- coding: utf-8 -*-
from openerp import api
from openerp.tests import TransactionCase
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError, AccessError

class TestMaterialOrder(TransactionCase):

    def setUp(self):
        super(TestMaterialOrder,self).setUp()

        # self.MaterialOrder = self.env['estate_stock.material_order']
        self.material_order = self.env.ref('estate_stock.mo_1')
        self.material_order.write({'type': 'estate'})

        # User
        User = self.env['res.users'].with_context({'no_reset_password': True})
        group_stock_user = self.ref('stock.group_stock_user')
        group_stock_assistant = self.ref('stock.group_stock_assistant')
        group_stock_manager = self.ref('stock.group_stock_manager')
        group_no_one = self.ref('base.group_no_one')

        self.user_stock_user = User.create({
            'name': 'User', 'login': 'user', 'alias_name': 'user', 'email': 'user@user.com',
            'groups_id': [(6, 0, [group_stock_user])]})
        self.user_stock_assistant = User.create({
            'name': 'Assistant', 'login': 'assistant', 'alias_name': 'assistant', 'email': 'assistant@assistant.com',
            'groups_id': [(6, 0, [group_stock_assistant])]})
        self.user_stock_manager = User.create({
            'name': 'Manager', 'login': 'manager', 'alias_name': 'manager', 'email': 'manager@manager.com',
            'groups_id': [(6, 0, [group_stock_manager])]})

        # self.product_a = self.env['product.product'].create({
        #     'name': 'product a',
        #     'type': 'product',
        #     'uom_id': self.ref('product.product_uom_kgm'),
        #     'uom_po_id': self.ref('product.product_uom_ton')
        # })
        # self.product_b = self.env['product.product'].create({
        #     'name': 'product b',
        #     'type': 'product',
        #     'uom_id': self.ref('product.product_uom_kgm'),
        #     'uom_po_id': self.ref('product.product_uom_ton')
        # })

        # update stock in hand
        # self.env['stock.quant'].create({
        #     'product_id': self.product_a.id,
        #     'location_id': self.env.ref('stock.stock_location_stock').id,
        #     'qty': 100.0})
        #
        # self.env['stock.quant'].create({
        #     'product_id': self.product_b.id,
        #     'location_id': self.env.ref('stock.stock_location_stock').id,
        #     'qty': 100.0})

        # self.vals = {
        #     'estate_id': self.ref('estate.estate'),
        #     'division_id': self.ref('estate.division_1'),
        #     'date_expected': '2017-01-01',
        #     'move_type': 'one',
        #     'picking_type_id': self.ref('stock.picking_type_internal'),
        #     'material_ids': [
        #         (0, 0, {
        #             'product_id': self.product_a.id,
        #             'product_uom_id': self.ref('product.product_uom_kgm'),
        #             'product_uom_qty': 1.5,
        #             'block_id': self.ref('estate.block_1')
        #         }),
        #         (0, 0, {
        #             'product_id': self.product_a.id,
        #             'product_uom_id': self.ref('product.product_uom_kgm'),
        #             'product_uom_qty': 1.5,
        #             'block_id': self.ref('estate.block_2')
        #         }),
        #         (0, 0, {
        #             'product_id': self.product_b.id,
        #             'product_uom_id': self.ref('product.product_uom_kgm'),
        #             'product_uom_qty': 1.5,
        #             'block_id': self.ref('estate.block_2')
        #         }),
        #         (0, 0, {
        #             'product_id': self.product_a.id,
        #             'product_uom_id': self.ref('product.product_uom_kgm'),
        #             'product_uom_qty': 4.5,
        #             'block_id': self.ref('estate.block_2')
        #         }),
        #     ]
        # }

        # self.material_order = self.MaterialOrder.with_context({'mail_create_nosubscribe': 'nosubscribe'}).sudo(self.user_stock_user).create(self.vals)


    # def test_00_create(self):
    #     """ Basic material order."""
    #     self.assertTrue(self.material_order)

    def test_00_demo_data(self):
        """ Check if demo data exist."""
        self.assertTrue(self.material_order)

    def test_01_action_confirm(self):
        """ Check action confirm."""

        # Check if access error raised
        with self.assertRaises(AccessError):
                self.material_order.sudo(self.user_stock_user).action_confirm()

        # Check if action confirm return confirm state
        self.material_order.sudo(self.user_stock_assistant).action_confirm()
        self.assertEqual(self.material_order.state, 'confirm')

    def test_01_action_approve(self):
        """ Check action approve."""
        self.assertEqual(self.material_order.type, 'estate')

        # Check if access error raised for stock user
        with self.assertRaises(AccessError):
            self.material_order.sudo(self.user_stock_user).action_approve()

        # Check if access error raised for stock assistant
        with self.assertRaises(AccessError):
            self.material_order.sudo(self.user_stock_assistant).action_approve()

        # Check if material order approved
        self.material_order.sudo(self.user_stock_manager).action_approve()
        self.assertEqual(self.material_order.state, 'approve')


    def test_01_action_draft(self):
        """ Redraft confirmed or approved material order."""

        self.material_order.sudo().action_confirm()

        # Check if access error raised for stock user
        with self.assertRaises(AccessError):
            self.material_order.sudo(self.user_stock_user).action_draft()

        # Check if access error raised for stock assistant
        with self.assertRaises(AccessError):
            self.material_order.sudo(self.user_stock_assistant).action_draft()

        # Check if material order change from confirm to draft
        self.material_order.sudo(self.user_stock_manager).action_draft()
        self.assertEqual(self.material_order.state, 'draft')

        # Check if redraft return validation error for approved material order
        self.material_order.sudo(self.user_stock_manager).action_approve()
        with self.assertRaises(ValidationError):
            self.material_order.sudo(self.user_stock_manager).action_draft()

    # def test_01_action_approve(self):
    #     """ Approve a material order."""
    #
    #     # Check warehouse company
    #     self.material_order.sudo(self.user_stock_manager).action_approve()
    #
    #     self.assertEqual(self.material_order.state, 'approve')
    #
    #     # Check stock picking created or not
    #     picking_ids = self.env['stock.picking'].search([('origin', '=', self.material_order.name)])
    #     print 'pickings %s' % self.material_order.stock_pickings([], self.material_order.name)
    #     self.assertEqual(len(picking_ids), 2)
    #
    #     # Check stock picking confirmed or not
    #     for picking in picking_ids:
    #         self.assertEqual(picking.state, 'confirmed')
    #
    #         # check stock picking required field
    #         self.assertEqual(picking.company_id.id, self.material_order.picking_type_id.warehouse_id.company_id.id)
    #         self.assertTrue(picking.move_type, 'No move type found.')
    #         self.assertTrue(picking.location_id, 'No source location found.')
    #         self.assertTrue(picking.location_dest_id, 'No destination location found.')
    #         self.assertTrue(picking.picking_type_id, 'No picking type found.')
    #         self.assertTrue(picking.priority, 'No priority defined.')
    #         self.assertTrue(picking.company_id, 'No company found.')
    #
    def test_01_action_cancel(self):
        """ Cancel material order."""
        self.material_order.sudo(self.user_stock_manager).action_approve()
        self.assertEqual(self.material_order.state, 'approve')

        # Check if cancel returned state = cancel
        self.material_order.sudo(self.user_stock_user).action_cancel()
        self.assertEqual(self.material_order.state, 'cancel')


        # Check if validation error raised as one picking has been done
        self.material_order.stock_pickings()[1].state = 'done'
        with self.assertRaises(ValidationError):
            self.material_order.action_cancel()

        # Check if cancel succeed
        self.material_order.stock_pickings()[1].state = 'assigned'
        self.material_order.action_cancel()
        self.assertEqual(self.material_order.state, 'cancel')

        for picking in self.material_order.stock_pickings():
            self.assertEqual(picking.state, 'cancel', 'Failed to cancel picking %s' % picking.name)

    def test_02_stock_pickings(self):
        """ Get stock picking from one material order"""

        self.material_order.sudo(self.user_stock_manager).action_approve()

        # Check if search without argument returned 2
        self.assertEqual(len(self.material_order.stock_pickings()), 2)

        # Check if search by state returned 2
        self.assertEqual(len(self.material_order.stock_pickings(state=['confirmed'])), 2)

        # Check if search by name returned 2
        self.assertEqual(len(self.material_order.stock_pickings(origin=self.material_order.name)), 2)

    def test_02_stock_moves(self):
        """ Get stock moves for one material order."""

        self.material_order.sudo().action_approve()

        # Check if stock moves returned 3
        self.assertEqual(len(self.material_order.stock_moves()), 3)

        # Check if stock moves returned 3 using material order name
        self.assertEqual(len(self.material_order.stock_moves(origin=self.material_order.name)), 3)
        self.assertEqual(len(self.material_order.stock_moves(state=['confirmed'])), 3)

        # Check if stock moves returned 2 confirmed
        stock_move_ids = self.material_order.stock_moves(origin=self.material_order.name)
        stock_move_ids[0].write({'state': 'done'})
        self.assertEqual(len(self.material_order.stock_moves(state=['done'], origin=stock_move_ids[0].picking_id.origin)), 1)




    def test_03_unlink(self):
        # Check if confirm, approve and done deleted or not
        self.material_order.state = 'confirm'
        with self.assertRaises(ValidationError):
            self.material_order.unlink()

        self.material_order.state = 'approve'
        with self.assertRaises(ValidationError):
            self.material_order.unlink()

        self.material_order.state = 'done'
        with self.assertRaises(ValidationError):
            self.material_order.unlink()

        self.material_order.state = 'draft'
        self.assertTrue(self.material_order.unlink())
