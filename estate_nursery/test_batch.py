from unittest import TestCase

from estate_nursery_batch import Batch

__author__ = 'odoo'


# class TestBatch(TestCase):
#     def test_negative_discr(self):
#         s = Batch
#         self.assertRaises(Exception)
#
#     def test_action_draft(self):
#         self.fail()
#
#     def test_action_confirmed(self):
#         self.fail()
#
#     def test_action_approved(self):
#         self.fail()
#
#     def test_action_receive(self):
#         self.fail()
#
#     def test_action_selection_next(self):
#         self.fail()
#
#     def test_action_create_selection(self):
#         self.fail()
#
#     def test_action_planted(self):
#         self.fail()


class TestBatch(TestCase):

    def test_negative_discr(self):
        s = Batch
        self.assertRaises(Exception)
    def test__compute_age_range(self):
        self.fail()

    def test__compute_total(self):
        self.fail()
