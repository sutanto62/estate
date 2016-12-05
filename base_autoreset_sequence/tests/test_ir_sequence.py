# -*- coding: utf-8 -*-
# Run with one of these commands:
#    > OPENERP_ADDONS_PATH='../../addons/trunk' OPENERP_PORT=8069 \
#      OPENERP_DATABASE=yy PYTHONPATH=. python tests/test_ir_sequence.py
#    > OPENERP_ADDONS_PATH='../../addons/trunk' OPENERP_PORT=8069 \
#      OPENERP_DATABASE=yy nosetests tests/test_ir_sequence.py
#    > OPENERP_ADDONS_PATH='../../../addons/trunk' OPENERP_PORT=8069 \
#      OPENERP_DATABASE=yy PYTHONPATH=../:. unit2 test_ir_sequence
# This assume an existing database.
import psycopg2
import psycopg2.errorcodes
import unittest
import openerp
import datetime, pytz


from openerp.tests import common

ADMIN_USER_ID = common.ADMIN_USER_ID

def registry(model):
    return openerp.modules.registry.RegistryManager.get(common.get_db_name())[model]

def cursor():
    return openerp.modules.registry.RegistryManager.get(common.get_db_name()).cursor()


def drop_sequence(code):
    cr = cursor()
    s = registry('ir.sequence')
    ids = s.search(cr, ADMIN_USER_ID, [('code', '=', code)])
    s.unlink(cr, ADMIN_USER_ID, ids)
    cr.commit()
    cr.close()

class test_ir_sequence_standard(unittest.TestCase):
    """ A few tests for a 'Standard' (i.e. PostgreSQL) sequence. """

    def test_ir_sequence_create(self):
        """ Try to create a sequence object. """
        cr = cursor()
        d = dict(code='test_sequence_type', name='Test sequence')
        c = registry('ir.sequence').create(cr, ADMIN_USER_ID, d, {})
        assert c
        cr.commit()
        cr.close()

    def test_ir_sequence_search(self):
        """ Try a search. """
        cr = cursor()
        ids = registry('ir.sequence').search(cr, ADMIN_USER_ID, [], {})
        assert ids
        cr.commit()
        cr.close()

    def test_ir_sequence_draw(self):
        """ Try to draw a number. """
        cr = cursor()
        n = registry('ir.sequence').next_by_code(cr, ADMIN_USER_ID, 'test_sequence_type', {})
        assert n
        cr.commit()
        cr.close()

    def test_ir_sequence_draw_twice(self):
        """ Try to draw a number from two transactions. """
        cr0 = cursor()
        cr1 = cursor()
        n0 = registry('ir.sequence').next_by_code(cr0, ADMIN_USER_ID, 'test_sequence_type', {})
        assert n0
        n1 = registry('ir.sequence').next_by_code(cr1, ADMIN_USER_ID, 'test_sequence_type', {})
        assert n1
        cr0.commit()
        cr1.commit()
        cr0.close()
        cr1.close()

    @classmethod
    def tearDownClass(cls):
        drop_sequence('test_sequence_type')

class test_ir_sequence_no_gap(unittest.TestCase):
    """ Copy of the previous tests for a 'No gap' sequence. """

    def test_ir_sequence_create_no_gap(self):
        """ Try to create a sequence object. """
        cr = cursor()
        d = dict(code='test_sequence_type_2', name='Test sequence',
            implementation='no_gap')
        c = registry('ir.sequence').create(cr, ADMIN_USER_ID, d, {})
        assert c
        cr.commit()
        cr.close()

    def test_ir_sequence_draw_no_gap(self):
        """ Try to draw a number. """
        cr = cursor()
        n = registry('ir.sequence').next_by_code(cr, ADMIN_USER_ID, 'test_sequence_type_2', {})
        assert n
        cr.commit()
        cr.close()

    def test_ir_sequence_draw_twice_no_gap(self):
        """ Try to draw a number from two transactions.
        This is expected to not work.
        """
        cr0 = cursor()
        cr1 = cursor()
        cr1._default_log_exceptions = False # Prevent logging a traceback
        with self.assertRaises(psycopg2.OperationalError) as e:
            n0 = registry('ir.sequence').next_by_code(cr0, ADMIN_USER_ID, 'test_sequence_type_2', {})
            assert n0
            n1 = registry('ir.sequence').next_by_code(cr1, ADMIN_USER_ID, 'test_sequence_type_2', {})
        self.assertEqual(e.exception.pgcode, psycopg2.errorcodes.LOCK_NOT_AVAILABLE, msg="postgresql returned an incorrect errcode")
        cr0.close()
        cr1.close()

    @classmethod
    def tearDownClass(cls):
        drop_sequence('test_sequence_type_2')

class test_ir_sequence_change_implementation(unittest.TestCase):
    """ Create sequence objects and change their ``implementation`` field. """

    def test_ir_sequence_1_create(self):
        """ Try to create a sequence object. """
        cr = cursor()
        d = dict(code='test_sequence_type_3', name='Test sequence')
        c = registry('ir.sequence').create(cr, ADMIN_USER_ID, d, {})
        assert c
        d = dict(code='test_sequence_type_4', name='Test sequence',
            implementation='no_gap')
        c = registry('ir.sequence').create(cr, ADMIN_USER_ID, d, {})
        assert c
        cr.commit()
        cr.close()

    def test_ir_sequence_2_write(self):
        cr = cursor()
        ids = registry('ir.sequence').search(cr, ADMIN_USER_ID,
            [('code', 'in', ['test_sequence_type_3', 'test_sequence_type_4'])], {})
        registry('ir.sequence').write(cr, ADMIN_USER_ID, ids,
            {'implementation': 'standard'}, {})
        registry('ir.sequence').write(cr, ADMIN_USER_ID, ids,
            {'implementation': 'no_gap'}, {})
        cr.commit()
        cr.close()

    def test_ir_sequence_3_unlink(self):
        cr = cursor()
        ids = registry('ir.sequence').search(cr, ADMIN_USER_ID,
            [('code', 'in', ['test_sequence_type_3', 'test_sequence_type_4'])], {})
        registry('ir.sequence').unlink(cr, ADMIN_USER_ID, ids, {})
        cr.commit()
        cr.close()

    @classmethod
    def tearDownClass(cls):
        drop_sequence('test_sequence_type_3')
        drop_sequence('test_sequence_type_4')

class test_ir_sequence_generate(unittest.TestCase):
    """ Create sequence objects and generate some values. """

    def test_ir_sequence_create(self):
        """ Try to create a sequence object. """
        cr = cursor()
        d = dict(code='test_sequence_type_5', name='Test sequence')
        c = registry('ir.sequence').create(cr, ADMIN_USER_ID, d, {})
        assert c
        cr.commit()
        cr.close()

        cr = cursor()
        f = lambda *a: registry('ir.sequence').next_by_code(cr, ADMIN_USER_ID, 'test_sequence_type_5', {})
        assert all(str(x) == f() for x in xrange(1,10))
        cr.commit()
        cr.close()

    def test_ir_sequence_create_no_gap(self):
        """ Try to create a sequence object. """
        cr = cursor()
        d = dict(code='test_sequence_type_6', name='Test sequence', implementation='no_gap')
        c = registry('ir.sequence').create(cr, ADMIN_USER_ID, d, {})
        assert c
        cr.commit()
        cr.close()

        cr = cursor()
        f = lambda *a: registry('ir.sequence').next_by_code(cr, ADMIN_USER_ID, 'test_sequence_type_6', {})
        assert all(str(x) == f() for x in xrange(1,10))
        cr.commit()
        cr.close()

    @classmethod
    def tearDownClass(cls):
        drop_sequence('test_sequence_type_5')
        drop_sequence('test_sequence_type_6')


class Test_ir_sequence_init(common.TransactionCase):

    def test_00(self):
        registry, cr, uid = self.registry, self.cr, self.uid

        # test if read statement return the good number_next value (from postgreSQL sequence and not ir_sequence value)
        sequence = registry('ir.sequence')
        # first creation of sequence (normal)
        values = {'number_next': 1,
                  'company_id': 1,
                  'padding': 4,
                  'number_increment': 1,
                  'implementation': 'standard',
                  'name': 'test-sequence-00'}
        seq_id = sequence.create(cr, uid, values)
        # Call get next 4 times
        sequence.next_by_id(cr, uid, seq_id)
        sequence.next_by_id(cr, uid, seq_id)
        sequence.next_by_id(cr, uid, seq_id)
        read_sequence = sequence.next_by_id(cr, uid, seq_id)
        # Read the value of the current sequence
        assert read_sequence == "0004", 'The actual sequence value must be 4. reading : %s' % read_sequence
        # reset sequence to 1 by write method calling
        sequence.write(cr, uid, [seq_id], {'number_next': 1})
        # Read the value of the current sequence
        read_sequence = sequence.next_by_id(cr, uid, seq_id)
        assert read_sequence == "0001", 'The actual sequence value must be 1. reading : %s' % read_sequence


class SequenceAutoreset(common.TransactionCase):

    def test_00_autoreset_month(self):
        """ Try using monthly autoreset sequence"""
        year = datetime.datetime.today().strftime('%Y')
        sequence_obj = self.env['ir.sequence']
        val = {
            'name': 'Sequence',
            'implementation': 'standard',
            'code': 'sequence',
            'prefix': 'SEQ/%(year)s/%(month)s/',
            'padding': 4,
            'number_increment': 1,
            'number_next_actual': 1,
            'auto_reset': True,
            'reset_period': 'month',
            'reset_time': '2016-02-01 17:00:00.0',
            'reset_init_number': 1,
        }

        now_utc = datetime.datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')
        ctx = {
            'ir_sequence_now': now_utc,
            'ir_sequence_reset': val['reset_time'],
        }

        # I created sequence object with autoreset
        seq_id = sequence_obj.create(val)
        seq_id.with_context(ctx)
        self.assertTrue(seq_id)

        # I tried for 4 sequences code
        seq_id.with_context(ir_sequence_date='2016-01-01').next_by_code('sequence')
        seq_id.with_context(ir_sequence_date='2016-01-02').next_by_code('sequence')
        seq_id.with_context(ir_sequence_date='2016-01-03').next_by_code('sequence')
        no_a = seq_id.with_context(ir_sequence_date='2016-01-04').next_by_code('sequence')
        self.assertEqual(no_a, 'SEQ/2016/01/0004')

        # I tried for next month
        seq_id.with_context(ir_sequence_date='2016-02-03').next_by_code('sequence')
        no_b = seq_id.with_context(ir_sequence_date='2016-02-04').next_by_code('sequence')
        self.assertEqual(no_b, 'SEQ/2016/02/0002')

    def test_01_autoreset_year(self):
        """ Try using yearly autoreset sequence"""
        year = datetime.datetime.today().strftime('%Y')
        sequence_obj = self.env['ir.sequence']
        val = {
            'name': 'Sequence',
            'implementation': 'standard',
            'code': 'sequence',
            'prefix': 'SEQ/%(year)s/%(month)s/',
            'padding': 4,
            'number_increment': 1,
            'number_next_actual': 1,
            'auto_reset': True,
            'reset_period': 'year',
            'reset_time': '2016-01-31 00:00:00.0',
            'reset_init_number': 1,
        }

        now_utc = datetime.datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')
        ctx = {
            'ir_sequence_now': now_utc,
            'ir_sequence_reset': val['reset_time'],
        }

        # I created sequence object with autoreset
        seq_id = sequence_obj.create(val)
        seq_id.with_context(ctx)
        self.assertTrue(seq_id)

        # I created sequence code for different date
        seq_id.with_context(ir_sequence_date='2015-02-03').next_by_code('sequence')
        seq_id.with_context(ir_sequence_date='2015-03-03').next_by_code('sequence')
        no_a = seq_id.with_context(ir_sequence_date='2015-04-04').next_by_code('sequence')
        self.assertEqual(no_a, 'SEQ/2015/04/0003')

        # I created sequence code over reset_time (time is 00:00:00.0)
        seq_id.with_context(ir_sequence_date='2016-02-01').next_by_code('sequence')
        no_b = seq_id.with_context(ir_sequence_date='2016-02-02').next_by_code('sequence')
        self.assertEqual(no_b, 'SEQ/2016/02/0002')


if __name__ == "__main__":
    unittest.main()
