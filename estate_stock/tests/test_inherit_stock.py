# -*- coding: utf-8 -*-
from openerp import api, _
from openerp.tests import TransactionCase
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError, AccessError

class TestStock(TransactionCase):

    def setUp(self):
        super(TestStock, self).setUp()

        self.MaterialOrder = self.env['estate_stock.material_order']

        # setup user and group
        User = self.env['res.users'].with_context({'no_reset_password': True})
        group_stock_user = self.ref('stock.group_stock_user')
        self.user_stock_user = User.create({
            'name': 'User', 'login': 'user', 'alias_name': 'user', 'email': 'user@user.com',
            'groups_id': [(6, 0, [group_stock_user])]})

        # setup product
        self.product_a = self.env['product.product'].create({
            'name': 'product a',
            'type': 'product',
            'uom_id': self.ref('product.product_uom_kgm'),
            'uom_po_id': self.ref('product.product_uom_ton')
        })
        self.product_b = self.env['product.product'].create({
            'name': 'product b',
            'type': 'product',
            'uom_id': self.ref('product.product_uom_kgm'),
            'uom_po_id': self.ref('product.product_uom_ton')
        })

        self.vals = {
            'estate_id': self.ref('estate.estate'),
            'division_id': self.ref('estate.division_1'),
            'date_expected': '2017-01-01',
            'move_type': 'one',
            'picking_type_id': self.ref('stock.picking_type_internal'),
            'material_ids': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_id': self.ref('product.product_uom_kgm'),
                    'product_uom_qty': 1.5,
                    'block_id': self.ref('estate.block_1')
                }),
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_id': self.ref('product.product_uom_kgm'),
                    'product_uom_qty': 1.5,
                    'block_id': self.ref('estate.block_2')
                }),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'product_uom_id': self.ref('product.product_uom_kgm'),
                    'product_uom_qty': 1.5,
                    'block_id': self.ref('estate.block_2')
                }),
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_id': self.ref('product.product_uom_kgm'),
                    'product_uom_qty': 4.5,
                    'block_id': self.ref('estate.block_2')
                }),
            ]
        }

        self.material_order = self.MaterialOrder.with_context({'mail_create_nosubscribe': 'nosubscribe'}).sudo(self.user_stock_user).create(self.vals)

    def test_00_action_assign(self):
        """ Check stock picking reserved."""

        self.material_order.sudo().action_approve()
        picking_ids = self.material_order.sudo().stock_pickings()
        self.assertTrue(picking_ids, 'Material order did not create stock picking.')

        # Check if reserve action raised or not (product has no stock yet)
        for picking in picking_ids:
            self.assertEqual(picking.state, 'confirmed', 'Picking should be at confirmed state.')
            for move in picking:
                self.assertEqual(move.product_id.qty_available, 0)
            with self.assertRaises(ValidationError):
                picking.action_assign()

        # Check if reserve action succeed or not
        self.env['stock.quant'].create({
            'product_id': self.product_a.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'qty': 100.0})

        self.env['stock.quant'].create({
            'product_id': self.product_b.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'qty': 100.0})

        for picking in picking_ids:
            self.assertTrue(picking.action_assign(), 'Picking failed to reserve.')

    def test_00_action_done(self):
        """ Check stock picking done."""

        self.env['stock.quant'].create({
            'product_id': self.product_a.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'qty': 100.0})
        self.env['stock.quant'].create({
            'product_id': self.product_b.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'qty': 100.0})

        # Approve material order
        self.material_order.sudo().action_approve()

        # Validate each picking
        picking_ids = self.material_order.stock_pickings()
        self.assertTrue(picking_ids, 'Material order did not create stock picking.')
        for picking in picking_ids:
            picking.action_assign()
            picking.do_new_transfer()
            for move in picking.move_lines:
                move.action_done()

        # Check if material order state followed picking or not.
        self.assertEqual(self.material_order.state, 'done', 'Material order state did not follow stock move\'s')

