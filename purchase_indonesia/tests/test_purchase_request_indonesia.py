# -*- coding: utf-8 -*-
from openerp.tools import SUPERUSER_ID
from openerp.tests.common import TransactionCase
from openerp.exceptions import ValidationError

class TestPurchaseRequestIndonesia(TransactionCase):

    def setUp(self):
        super(TestPurchaseRequestIndonesia, self).setUp()
        self.PurchaseRequest = self.env['purchase.request']
        self.PurchaseRequestLine = self.env['purchase.request.line']
        self.Employee = self.env['hr.employee']
        self.Office = self.env['hr_indonesia.office']
        self.PurchaseIndonesiaType = self.env['purchase.indonesia.type']

        User = self.env['res.users'].with_context({'no_reset_password': True})
        group_user = self.ref('base.group_user')
        group_purchase_request_user = self.ref('purchase_request.group_purchase_request_user')

        self.purchase_user = User.create({
            'name': 'User', 'login': 'user', 'alias_name': 'user', 'email': 'user@user.com',
            'groups_id': [(6, 0, [group_user, group_purchase_request_user])]})

        self.company_id = self.env['res.company'].create({
            'name': 'Agro Palma',
            'code': 'AP',
            'parent_id' : 1
        })

        self.company_id_2 = self.env['res.company'].create({
            'name': 'Tri Palma',
            'code': 'TP',
            'parent_id' : 1
        })

        self.company_id_3 = self.env['res.company'].create({
            'name': 'Agro',
            'code': 'A',
            'parent_id' : 1
        })

        self.warehouse_id = self.env['stock.warehouse'].create({
            'name': 'WH Agro Palma',
            'code': 'WHAP',
            'company_id': self.company_id.id,
        })

        self.warehouse_id_2 = self.env['stock.warehouse'].create({
            'name': 'WH Tri Palma',
            'code': 'WHTP',
            'company_id': self.company_id_2.id,
        })

        self.picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'incoming'), \
                                          ('warehouse_id.company_id', '=', self.company_id.id)])
        self.picking_type_id_2 = self.env['stock.picking.type'].search([('code', '=', 'incoming'), \
                                          ('warehouse_id.company_id', '=', self.company_id_2.id)])

        self.office_level_id = self.Office.create({
            'name' : 'Estate',
            'code' : 'KOKB'
        })

        self.employee_user = self.Employee.create({
            'name' : 'User',
            'user_id' : self.purchase_user.id,
            'office_level_id' : self.office_level_id.id
        })

        self.purchase_indonesia_type_id = self.PurchaseIndonesiaType.create({
            'name' : 'Normal'
        })

        self.vals1 = {
            'type_purchase': self.purchase_indonesia_type_id.id,
            'type_functional': 'general',
            'employee_id': self.employee_user.id,
            # 'type_location': 'Estate',
            # 'code': 'KOKB',
            'type_product': 'product',
            'type_budget': 'not',
            # 'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'picking_type_id': self.picking_type_id.id,
            'requested_by': SUPERUSER_ID,
            'company_id' : self.company_id.id
        }
        self.purchase_request_id = self.PurchaseRequest.sudo(self.purchase_user).create(self.vals1)

        self.vals2 = {
            'request_id': self.purchase_request_id.id,
            'product_id': self.env.ref('product.product_product_13').id,
            'product_uom_id': self.env.ref('product.product_uom_unit').id,
            'product_qty': 5.0,
        }
        self.PurchaseRequestLine.sudo(self.purchase_user).create(self.vals2)

    def test_00_create(self):
        """ Basic purchase request. """
        self.assertTrue(self.purchase_request_id)

    def test_01_purchase_request_status(self):
        """ Check if purchase request is editable."""
        self.assertEqual(
            self.purchase_request_id.is_editable, True,
            'Should be editable')

    def test_02_button_to_approve(self):
        """ Approve a purchase request. """
        self.purchase_request_id.button_to_approve()
        self.assertEqual(
            self.purchase_request_id.state, 'to_approve',
            'Should be in state to_approve')

        self.assertEqual(
            self.purchase_request_id.is_editable, False,
            'Should not be editable')

    def test_03_button_draft(self):
        """ Redraft a purchase request """
        self.purchase_request_id.button_draft()
        self.assertEqual(
            self.purchase_request_id.is_editable, True,
            'Should be editable')

        self.assertEqual(
            self.purchase_request_id.state, 'draft',
            'Should be in state draft')

    def test_04_unlink(self):
        """ Check delete if state draft """
        self.purchase_request_id.state = 'draft'
        self.assertTrue(self.PurchaseRequestLine.unlink())

    def test_05_get_office_level_id(self):
        # This function is used to test default function on 'type_location' fields.
        self.purchase_request_id._get_office_level_id()
        self.assertEqual(
            self.purchase_request_id.type_location, self.office_level_id.name,'Could not get default Type Location'
        )

    def test_06_get_office_level_id_code(self):
        # this function is used to test default function on 'location' fields.
        self.purchase_request_id._get_office_level_id_code()
        self.assertEqual(
            self.purchase_request_id.code, self.office_level_id.code, 'Get not get default Location'
        )

    def test_07_onchange_company_id(self):
        # this function is used to test picking_type_id value if company_id changed
        self.purchase_request_id.company_id = self.company_id_2.id
        self.purchase_request_id._onchange_company_id()
        self.assertEqual(self.purchase_request_id.picking_type_id.id,
                         self.picking_type_id_2.id,
                         'Could not get picking_type_id based on company_id')

        # if picking_type_id not found because company_id does not have warehouse
        self.purchase_request_id.company_id = self.company_id_3.id
        with self.assertRaises(ValidationError):
            self.purchase_request_id._onchange_company_id()