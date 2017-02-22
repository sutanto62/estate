from openerp.tests import common
from openerp.tools import SUPERUSER_ID


class TestPurchaseRequestIndonesia(common.TransactionCase):

    def setUp(self):
        super(TestPurchaseRequestIndonesia, self).setUp()
        self.purchase_request = self.env['purchase.request']
        self.purchase_request_line = self.env['purchase.request.line']

    def test_purchase_request_status(self):
        vals = {
            'type_purchase':1,
            'type_functional':'general',
            'department_id':40,
            'employee_id': 	776,
            'type_location':'Estate',
            'code':'KOKB',
            'type_product':'product',
            'type_budget':'not',
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'requested_by': SUPERUSER_ID,
        }
        purchase_request = self.purchase_request.create(vals)
        vals = {
            'request_id': purchase_request.id,
            'product_id': self.env.ref('product.product_product_13').id,
            'product_uom_id': self.env.ref('product.product_uom_unit').id,
            'product_qty': 5.0,
        }
        self.purchase_request_line.create(vals)

        purchase_request._get_office_level_id()
        self.assertEqual(
            purchase_request.code,'Estate','Get Employee Code'
        )
        purchase_request._get_office_level_id_code()
        self.assertEqual(
            purchase_request.code,'KOKB','Get Employee Code'
        )

        self.assertEqual(
            purchase_request.is_editable, True,
            'Should be editable')

        purchase_request.button_to_approve()

        self.assertEqual(
            purchase_request.state, 'to_approve',
            'Should be in state to_approve')

        self.assertEqual(
            purchase_request.is_editable, False,
            'Should not be editable')

        purchase_request.button_draft()
        self.assertEqual(
            purchase_request.is_editable, True,
            'Should be editable')

        self.assertEqual(
            purchase_request.state, 'draft',
            'Should be in state draft')
        self.purchase_request_line.unlink()