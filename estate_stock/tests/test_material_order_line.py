# -*- coding: utf-8 -*-
from openerp import api
from openerp.tests import TransactionCase
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError, AccessError

class TestMaterialOrderLine(TransactionCase):

    def setUp(self):
        super(TestMaterialOrderLine,self).setUp()

        self.MaterialOrder = self.env['estate_stock.material_order']

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

        # update stock in hand
        self.env['stock.quant'].create({
            'product_id': self.product_a.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'qty': 100.0})

        self.env['stock.quant'].create({
            'product_id': self.product_b.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'qty': 100.0})

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

    def test_00_create(self):
        """ Basic material order."""
        self.assertTrue(self.material_order)

    def test_01_compute_partner_id(self):
        """ Check partner"""

        # Check whether material return main partner
        for material in self.material_order.material_ids:
            # self.assertTrue(True)
            # material._compute_partner_id()
            self.assertEqual(material.partner_id.id, self.ref('base.main_partner'))
