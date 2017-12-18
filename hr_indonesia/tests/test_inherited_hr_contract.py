# -*- coding: utf-8 -*-

from openerp import api
from openerp.tests import TransactionCase
from openerp.exceptions import ValidationError, AccessError
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT


class TestContract(TransactionCase):

    def setUp(self):
        super(TestContract, self).setUp()

        self.Contract = self.env['hr.contract'].sudo()
        self.Employee = self.env['hr.employee'].sudo()

        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']

        # created employee
        self.employee_id = employee_obj.sudo().create({
            'name': 'Employee'
        })

        # created contract
        self.contract_type_id = self.env['hr.contract.type'].sudo().create({
            'name': 'Estate Worker'
        })
        self.val = {
            'name': 'Employee Contract',
            'employee_id': self.employee_id.id,
            'wage': 3100000,
            'date_start': (datetime.today() + relativedelta.relativedelta(month=1, day=1)).strftime(DF),
            'date_end': (datetime.today() + relativedelta.relativedelta(years=1, month=1, day=1, days=-1)).strftime(DF),
            'type_id': self.contract_type_id.id
        }

    def test_00_setup(self):
        contract_id = self.Contract.create(self.val)
        self.assertTrue(contract_id)

    def test_01_is_probation(self):
        """ Check probation """
        contract_id = self.Contract.create(self.val)
        self.assertTrue(contract_id)
        self.assertFalse(contract_id.is_probation())

        # complete trial date
        contract_id.write({
            'trial_date_start': (datetime.today() + relativedelta.relativedelta(months=-1)).strftime(DF),
            'trial_date_end': (datetime.today() + relativedelta.relativedelta(months=1)).strftime(DF),
        })
        self.assertTrue(contract_id.is_probation())

        # no end date
        contract_id.write({
            'trial_date_start': (datetime.today() + relativedelta.relativedelta(months=-1)).strftime(DF),
            'trial_date_end': False
        })
        self.assertFalse(contract_id.is_probation())

        # no start date
        contract_id.write({
            'trial_date_start': False,
            'trial_date_end': (datetime.today() + relativedelta.relativedelta(months=1)).strftime(DF)
        })
        self.assertFalse(contract_id.is_probation())

    def test_01_is_probation_employee(self):
        """" Checked probation."""

        # created 3 months probation
        trial = {
            'trial_date_start': (datetime.today() + relativedelta.relativedelta(month=1, day=1)).strftime(DF),
            'trial_date_end': (datetime.today() + relativedelta.relativedelta(month=4, day=1, days=-1)).strftime(DF)
        }
        self.val.update(**trial)
        contract_1 = self.Contract.create(self.val)

        # checked date within probation
        date_checked = datetime.today() + relativedelta.relativedelta(month=1, day=15)
        self.assertTrue(contract_1.is_probation(date_checked))

        # checked date after probation
        date_checked = datetime.today() + relativedelta.relativedelta(month=4, day=1)
        self.assertFalse(contract_1.is_probation(date_checked))

        # checked date before probation
        date_checked = datetime.today() + relativedelta.relativedelta(years=-1)
        self.assertFalse(contract_1.is_probation(date_checked))

        # checked no probation date
        contract_1.write({'trial_date_start': None, 'trial_date_end': None})
        self.assertFalse(contract_1.is_probation(date_checked))



    def test_01_constrains_contract(self):
        """ Check new contract less than or equal previous contract start date."""

        # contract with specific date and end
        contract_1 = self.Contract.create(self.val)
        self.assertTrue(contract_1)

        # less than or equal to previous date start
        self.val['date_start'] = (datetime.today() + relativedelta.relativedelta(month=1, day=1)).strftime(DF)
        with self.assertRaises(ValidationError):
            self.Contract.with_context({'mail_create_nosubscribe': 'nosubscribe'}).create(self.val)

        # less than or equal to previous date end
        self.val['date_start'] = (datetime.today() + relativedelta.relativedelta(years=1, month=1, day=1, days=-1)).strftime(DF)
        with self.assertRaises(ValidationError):
            self.Contract.with_context({'mail_create_nosubscribe': 'nosubscribe'}).create(self.val)

    def test_01_constrain_contract_without_end(self):
        """ Check new contract against endless old contract"""

        # created no end date contract
        del self.val['date_end']
        contract_1 = self.Contract.create(self.val)
        self.assertTrue(contract_1)

        # less than or equal to previous date start
        self.val['date_start'] = (datetime.today() + relativedelta.relativedelta(month=1, day=1)).strftime(DF)
        with self.assertRaises(ValidationError):
            self.Contract.with_context({'mail_create_nosubscribe': 'nosubscribe'}).create(self.val)

    def test_02_current(self):
        """ Check get active contract for contract with start and end date."""

        # I created two consecutive a year contract (current and next year)
        self.val.update(
            name='Employee Contract A',
            date_start=(datetime.today() + relativedelta.relativedelta(month=1, day=1)).strftime(DF),
            date_end=(datetime.today() + relativedelta.relativedelta(years=1, month=1, day=1, days=-1)).strftime(DF)
        )
        contract_1 = self.Contract.create(self.val)

        self.val.update(
            name='Employee Contract B',
            date_start=(datetime.today() + relativedelta.relativedelta(years=1, month=1, day=1)).strftime(DF),
            date_end=(datetime.today() + relativedelta.relativedelta(years=2, month=1, day=1, days=-1)).strftime(DF)
        )
        contract_2 = self.Contract.with_context({'mail_create_nosubscribe': 'nosubscribe'}).create(self.val)

        self.assertTrue(contract_1)
        self.assertTrue(contract_2)

        # checked active contract, period year
        contract_id = self.Contract.current(self.employee_id)
        self.assertEqual(contract_id.name, 'Employee Contract A')

        # I created two consecutive half year contract (within same year)
        contract_1.unlink()
        contract_2.unlink()

        self.val.update(
            name='Employee Contract C',
            date_start=(datetime.today() + relativedelta.relativedelta(month=1, day=1)).strftime(DF),
            date_end=(datetime.today() + relativedelta.relativedelta(month=7, day=1, days=-1)).strftime(DF)
        )
        contract_1 = self.Contract.with_context({'mail_create_nosubscribe': 'nosubscribe'}).create(self.val)

        self.val.update(
            name='Employee Contract D',
            date_start=(datetime.today() + relativedelta.relativedelta(month=7, day=1)).strftime(DF),
            date_end=(datetime.today() + relativedelta.relativedelta(years=1, month=1, day=1, days=-1)).strftime(DF)
        )
        contract_2 = self.Contract.with_context({'mail_create_nosubscribe': 'nosubscribe'}).create(self.val)

        # I checked active contract, period year
        contract_id = self.Contract.current(self.employee_id)
        self.assertEqual(contract_id.name, 'Employee Contract D')

    def test_02_current_no_date_end(self):
        """ Check get active contract without end date."""

        # I created two consecutive a year contract (current and next year)
        self.val.update(
            name='Employee Contract E',
            date_start=(datetime.today() + relativedelta.relativedelta(month=1, day=1)).strftime(DF),
            date_end=False
        )
        contract_1 = self.Contract.create(self.val)

        self.val.update(
            name='Employee Contract F',
            date_start=(datetime.today() + relativedelta.relativedelta(years=1, month=1, day=1)).strftime(DF),
            date_end=False
        )
        contract_2 = self.Contract.with_context({'mail_create_nosubscribe': 'nosubscribe'}).create(self.val)

        self.assertTrue(contract_1)
        self.assertTrue(contract_2)

        # checked active contract, period year
        contract_id = self.Contract.current(self.employee_id)
        self.assertEqual(contract_id.name, 'Employee Contract E')

        # I created two consecutive half year contract (within same year)
        contract_1.unlink()
        contract_2.unlink()

        self.val.update(
            name='Employee Contract G',
            date_start=(datetime.today() + relativedelta.relativedelta(month=1, day=1)).strftime(DF),
            date_end=False
        )
        contract_1 = self.Contract.with_context({'mail_create_nosubscribe': 'nosubscribe'}).create(self.val)

        self.val.update(
            name='Employee Contract H',
            date_start=(datetime.today() + relativedelta.relativedelta(month=4, day=1)).strftime(DF),
            date_end=False
        )
        contract_2 = self.Contract.with_context({'mail_create_nosubscribe': 'nosubscribe'}).create(self.val)

        self.val.update(
            name='Employee Contract J',
            date_start=(datetime.today() + relativedelta.relativedelta(month=7, day=1)).strftime(DF),
            date_end=False
        )
        contract_3 = self.Contract.with_context({'mail_create_nosubscribe': 'nosubscribe'}).create(self.val)

        # I checked active contract, period year
        march = datetime.today() + relativedelta.relativedelta(month=3, day=15)
        may = datetime.today() + relativedelta.relativedelta(month=5, day=15)
        contract_march = self.Contract.current(self.employee_id, march)
        self.assertEqual(contract_march.name, 'Employee Contract G')
        contract_may =  self.Contract.current(self.employee_id, may)
        self.assertEqual(contract_may.name, 'Employee Contract H')


