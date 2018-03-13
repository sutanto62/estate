# -*- coding: utf-8 -*-
from openerp.tools import SUPERUSER_ID
from openerp.tests.common import TransactionCase
from openerp.exceptions import ValidationError

class TestSlaVendorManagement(TransactionCase):
    def setUp(self):
        super(TestSlaVendorManagement, self).setUp()
        self.SlaVendorManagement = self.env['sla.vendor.management']
        self.local_vendor_id = self.ref('purchase_indonesia.local_rec')
        self.inter_island_vendor_id = self.ref('purchase_indonesia.inter_island_rec')
        self.inter_country_vendor_id = self.ref('purchase_indonesia.inter_country_rec')

    def test_01_get_available_code(self):
        # Check against existing code.
        self.assertEqual(self.SlaVendorManagement.get_available_code(1, 'inter_island').id, 2, 'Code not found!')
        # Check new code
        self.assertEqual(self.SlaVendorManagement.get_available_code(1, 'inter_galaxy').id, False, 'Code found!')