from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError
from openerp import SUPERUSER_ID
from datetime import datetime, timedelta, tzinfo
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from math import floor
import pytz

class TestInheritPurchaseOrder(TransactionCase):

    def setUp(self):
        super(TestInheritPurchaseOrder, self).setUp()
        self.purchase_order = self.env['purchase.order']

        self.purchase_request = self.env['purchase.request'].create(dict(
            name = 'Purchase test case',
            type_product = 'service'
        ))

    # def test_01_validation_srn(self):
    #
    #     # I checked attendance
    #     self.purchase_order.search([('validation','=',)])
    #     for attendance in fingerprint.attendance_ids:
    #         self.assertTrue(attendance)
    #         self.assertTrue(attendance.action in ('sign_in', 'sign_out', 'action'), 'Action did not belong to in/out/action.')
    #     self.assertEqual(len(fingerprint.attendance_ids), 2, 'Fingerprint did not create in and out attendance.')