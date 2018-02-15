# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError

class TestBlockTemplate(TransactionCase):

    def setUp(self):
        super(TestBlockTemplate, self).setUp()

        self.Block = self.env['estate.block.template']

        self.estate = self.Block.sudo().create({
            'name': 'Estate',
            'estate_location': True,
            'estate_location_level': '1',
            'estate_location_type': 'planted'
        })
        self.d1 = self.Block.sudo().create({
            'name': 'Division 1',
            'estate_location': True,
            'estate_location_level': '2',
            'estate_location_type': 'planted',
            'location_id': self.estate.inherit_location_id.id
        })
        self.d1a = self.Block.sudo().create({
            'name': 'Block 1A',
            'estate_location': True,
            'estate_location_level': '3',
            'estate_location_type': 'planted',
            'location_id': self.d1.inherit_location_id.id
        })
        self.d1b = self.Block.sudo().create({
            'name': 'Block 1B',
            'estate_location': True,
            'estate_location_level': '3',
            'estate_location_type': 'planted',
            'location_id': self.d1.inherit_location_id.id
        })
        self.d1b1 = self.Block.sudo().create({
            'name': 'Block 1B.1',
            'estate_location': True,
            'estate_location_level': '4',
            'estate_location_type': 'planted',
            'location_id': self.d1b.inherit_location_id.id
        })

        # double division level
        self.dd1 = self.Block.sudo().create({
            'name': 'Sub Division 1',
            'estate_location': True,
            'estate_location_level': '2',
            'estate_location_type': 'planted',
            'location_id': self.d1.inherit_location_id.id
        })
        self.dd1a = self.Block.sudo().create({
            'name': 'Block DD1.1',
            'estate_location': True,
            'estate_location_level': '2',
            'estate_location_type': 'planted',
            'location_id': self.dd1.inherit_location_id.id
        })

    def test_get_parent_location(self):
        """ Check get parent location"""

        # Check if return False
        self.assertEqual(self.estate.get_parent_location(), False)

        # Check if return estate
        self.assertEqual(self.d1.get_parent_location().name, self.estate.inherit_location_id.name)
        self.assertEqual(self.d1b.get_parent_location('1').name, self.estate.inherit_location_id.name)
        self.assertEqual(self.d1b1.get_parent_location('1').name, self.estate.inherit_location_id.name)
        self.assertEqual(self.dd1a.get_parent_location('1').name, self.estate.inherit_location_id.name)

        # Check if return division
        self.assertEqual(self.d1b.get_parent_location().name, self.d1.inherit_location_id.name)
        self.assertEqual(self.d1b1.get_parent_location('2').name, self.d1.inherit_location_id.name)

        # Check if return direct division
        self.assertEqual(self.dd1a.get_parent_location('2').name, self.dd1.inherit_location_id.name)

        # Check if estate return False
        self.assertEqual(self.estate.get_parent_location('1'), False)
        self.assertEqual(self.estate.get_parent_location('5'), False)
