# -*- coding: utf-8 -*-

import logging
from openerp import models, api

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def _post_validate(self):
        """ Error when post account move with different company."""
        if not self._context.get('check_move_validity'):
            self.assert_balanced()
            return self._check_lock_date()
        else:
            return super(AccountMove, self)._post_validate()

