# -*- coding: utf-8 -*-

from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError

class TestMasterActivity(TransactionCase):

    def setUp(self):
        super(TestMasterActivity, self).setUp()
        self.MasterActivity = self.env['estate.activity']
        self.Block = self.env['estate.block.template']
        self.StockLocation = self.env['stock.location']

        vals = {
            'name': 'Activity',
            'type': 'normal',
            'qty_base': 7.5,
            'qty_base_min': 5,
            'qty_base_max': 10,
            'ratio_min': 0,
            'ratio_max': 0,
            'parameter_weight_ids': [
                (0, 0, {
                    'parameter_id': self.env.ref('estate.parameter_soil').id,
                    'weight': 0.2
                })
            ],
            'activity_norm_ids': [
                (0, 0, {
                    'parameter_id': self.env.ref('estate.parameter_soil').id,
                    'parameter_value_id': self.env.ref('estate.parameter_value_mineral').id,
                    'coefficient': 1.00,
                    'ratio_base': 0,
                    'qty_base': 0,
                }),
                (0, 0, {
                    'parameter_id': self.env.ref('estate.parameter_soil').id,
                    'parameter_value_id': self.env.ref('estate.parameter_value_gambut').id,
                    'coefficient': 0.5,
                    'ratio_base': 0,
                    'qty_base': 0,
                })
            ]
        }

        self.master = self.MasterActivity.create(vals)

    def test_00_check_parameter_value(self):
        """ Check parameter and parameter's value constrains """

        vals = {
            'name': 'Activity',
            'type': 'normal',
            'wage_method': 'standard',
            'qty_base': 1,
            'parameter_weight_ids': [
                (0, 0, {
                    'parameter_id': self.env.ref('estate.parameter_soil').id,
                    'weight': 0.2
                })
            ],
            'activity_norm_ids': [
                (0, 0, {
                    'parameter_id': self.env.ref('estate.parameter_soil').id,
                    'parameter_value_id': self.env.ref('estate.parameter_value_mineral').id,
                    'coefficient': 1.00,
                    'ratio_base': 0,
                    'qty_base': 0,
                })
            ]
        }

        self.assertTrue(self.MasterActivity.create(vals), 'Estate: _check_parameter_value constrains did not work')

    def test_00_check_double_parameter_value(self):
        """ Check double parameter and parameter's value constrains """

        vals = {
            'name': 'Activity',
            'type': 'normal',
            'parameter_weight_ids': [
                (0, 0, {
                    'parameter_id': self.env.ref('estate.parameter_soil').id,
                    'weight': 0.2
                })
            ],
            'activity_norm_ids': [
                (0, 0, {
                    'parameter_id': self.env.ref('estate.parameter_soil').id,
                    'parameter_value_id': self.env.ref('estate.parameter_value_mineral').id,
                    'wage_method': 'standard',
                    'coefficient': 1.00,
                    'ratio_base': 0,
                    'qty_base': 1,
                })
            ]
        }
        # Check error on double parameter value
        with self.assertRaises(ValidationError):
            vals['activity_norm_ids'] += [
                (0, 0, {
                    'parameter_id': self.env.ref('estate.parameter_soil').id,
                    'parameter_value_id': self.env.ref('estate.parameter_value_mineral').id,
                    'coefficient': 1.00,
                    'ratio_base': 0,
                    'qty_base': 0,
                })]
            self.MasterActivity.create(vals)
            print 'create #2'

    def test_00_check_not_listed_parameter_value(self):
        """ Check parameter and parameter's value constrains """

        vals = {
            'name': 'Activity',
            'type': 'normal',
            'wage_method': 'standard',
            'qty_base': 1,
            'parameter_weight_ids': [
                (0, 0, {
                    'parameter_id': self.env.ref('estate.parameter_soil').id,
                    'weight': 0.2
                })
            ],
            'activity_norm_ids': [
                (0, 0, {
                    'parameter_id': self.env.ref('estate.parameter_soil').id,
                    'parameter_value_id': self.env.ref('estate.parameter_value_mineral').id,
                    'coefficient': 1.00,
                    'ratio_base': 0,
                    'qty_base': 0,
                })
            ]
        }
        # Check not listed parameter
        with self.assertRaises(ValidationError):
            vals['activity_norm_ids'] += [
                (0, 0, {
                    'parameter_id': self.env.ref('estate.parameter_topography').id,
                    'parameter_value_id': self.env.ref('estate.parameter_value_hilly').id,
                    'coefficient': 1.00,
                    'ratio_base': 0,
                    'qty_base': 0,
                })]
            self.MasterActivity.create(vals)
            print 'create #3'

    def test_00_check_min_greater_max(self):
        """ Check error if minimum greater than maximum"""

        vals = {
            'name': 'Activity',
            'type': 'normal',
            'qty_base': 0,
            'qty_base_min': 0,
            'qty_base_max': 0
        }

        # Min greater than max
        with self.assertRaises(ValidationError):
            vals['qty_base_min'] = 5
            vals['qty_base_max'] = 1
            self.MasterActivity.create(vals)

    def test_00_check_base_less_min(self):
        """ Check error if base less than minimum"""
        vals = {
            'name': 'Activity',
            'type': 'normal',
            'qty_base': 0,
            'qty_base_min': 0,
            'qty_base_max': 0
        }
        # Base less than min
        with self.assertRaises(ValidationError):
            vals['qty_base'] = 1
            vals['qty_base_min'] = 5
            vals['qty_base_max'] = 10
            self.MasterActivity.create(vals)

    def test_00_check_base_greater_max(self):
        """ Check error if base greater than maximum"""
        vals = {
            'name': 'Activity',
            'type': 'normal',
            'qty_base': 0,
            'qty_base_min': 0,
            'qty_base_max': 0
        }
        # # Base greater than max
        with self.assertRaises(ValidationError):
            vals['qty_base'] = 15
            vals['qty_base_min'] = 5
            vals['qty_base_max'] = 10
            self.MasterActivity.create(vals)

    def test_00_check_weight(self):
        vals = {
            'name': 'Activity',
            'type': 'normal',
            'parameter_weight_ids': [
                (0, 0, {
                    'parameter_id': self.env.ref('estate.parameter_soil').id,
                    'weight': 0.9
                }),
                (0, 0, {
                    'parameter_id': self.env.ref('estate.parameter_topography').id,
                    'weight': 0.9
                })
            ]}

        # Total parameter weight should not exceed 1
        with self.assertRaises(ValidationError):
            self.MasterActivity.create(vals)

    def test_00_complete_name(self):
        parent_vals = {
            'name': 'Parent',
            'type': 'view',
        }
        a_parent = self.MasterActivity.create(parent_vals)
        child_vals = {
            'name': 'Child',
            'type': 'normal',
            'wage_method': 'standard',
            'qty_base': 1,
            'parent_id': a_parent.id
        }
        activity = self.MasterActivity.create(child_vals)
        self.assertEqual(activity.complete_name, 'Parent / Child', 'Estate: _complete_name failed.')

    # def test_master_compute_norm(self):
    #     for norm in self.master.activity_norm_ids:
    #         if (norm['parameter_id']['name'] == 'Soil Type' and norm['parameter_value_id']['name'] == 'Mineral'):
    #             self.assertEqual(norm['qty_base'], 2, 'Estate: _compute_norm failed compute qty_base')
    #             self.assertEqual(norm['ratio_base'], 0.02, 'Estate: _compute_norm failed compute ratio_base')
    #
    #         if (norm['parameter_id']['name'] == 'Soil Type' and norm['parameter_value_id']['name'] == 'Gambut'):
    #             self.assertEqual(norm['qty_base'], 1.5, 'Estate: _compute_norm failed compute qty_base')
    #             self.assertEqual(norm['ratio_base'], 0.03, 'Estate: _compute_norm failed compute ratio_base')

    def test_00_compute_ratio(self):
        # Check _check_qty_base
        self.assertTrue(self.master._check_qty_base(), 'Estate: _check_qty_base failed')

        # Check _compute_ratio_min and _compute_ratio_max
        self.assertEqual(self.master.ratio_min, 0.2, 'Estate: _compute_ratio_min failed.')
        self.assertEqual(self.master.ratio_max, 0.1, 'Estate: _compute_ratio_max failed.')

    def test_00_get_qty(self):
        self.assertTrue(self.master.qty_base, 'Estate: _get_qty did not return qty_base')

    def test_00_get_ratio(self):
        self.assertTrue(self.master.ratio_min, 'Estate: _get_ratio did not return ratio_min')

    def test_01_check_coefficient(self):
        # Check 0 < X < 1
        self.assertTrue(self.master.activity_norm_ids[0].write({'coefficient': 0.5}))

        # Check X < 0 - false
        with self.assertRaises(ValidationError):
            self.master.activity_norm_ids[0].write({'coefficient': -2})

        # Check X > 1 - false
        with self.assertRaises(ValidationError):
            self.master.activity_norm_ids[0].write({'coefficient': 2})

    def test_01_compute_qty_ratio(self):
        self.assertEqual(self.master.parameter_weight_ids[0]['weight'], 0.2, 'Estate: parameter weight did not return 2')
        self.assertEqual(self.master.activity_norm_ids[0]['qty_base'], 2, 'Estate: _compute_qty_ratio did not return 2')
        self.assertEqual(self.master.activity_norm_ids[0]['ratio_base'], 0.5, 'Estate: _compute_qty_ratio did not return 0.2')

        # Imitate no parameter and parameter value defined
        # self.master.activity_norm_ids[0].write({'parameter_id': False, 'parameter_value_id': False})
        # self.master.activity_norm_ids[0]._compute_qty_ratio()
        # print 'Activity Norm 0 %s' % self.master.activity_norm_ids[0]['qty_base']

    def test_01_compute_norm(self):
        for norm in self.master.activity_norm_ids:
            norm._compute_qty_ratio()
        self.assertEqual(self.master.activity_norm_ids[0]['qty_base'], 2, 'Estate: _compute_qty_ratio did not return 2')
        self.assertEqual(self.master.activity_norm_ids[0]['ratio_base'], 0.5, 'Estate: _compute_qty_ratio did not return 0.2')

    def test_02_get_stand_hectare(self):

        block_val = {
            'name': 'Estate',
            'scrap_location': False,
            'qty_sph_standard': 130
        }
        block = self.Block.create(block_val)

        # Check stock location creation
        self.assertTrue(block.inherit_location_id, 'Estate: create failed to inherit stock location record')

    def test_03_get_estate(self):
        block_id = self.env.ref('stock.stock_block_1')
        estate_id = self.StockLocation.get_estate(block_id.id)
        # self.assertEqual(estate_id.name, 'LYD', 'Estate: stock_location.get_estate failed to get estate location (LYD)')
        self.assertTrue(estate_id, 'Cannot find stock loctaion')

    def test_04_get_current_overtime(self):
        regional_wage = self.env['estate.wage']
        self.assertEqual(regional_wage.get_current_overtime(self.env.ref('estate.estate_stock_location')), 8000)
