# -*- coding: utf-8 -*-
import re
from StringIO import StringIO
import base64
import datetime
import dateutil
import time
import logging
import simplejson
from lxml import etree
from openerp import tools
from openerp import api, models, fields
import openerp.addons.auth_signup.res_users as res_users
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _
from openerp.addons.base.ir.ir_qweb import QWebContext
import openerp

from openerp.tools.translate import xml_translate

_logger = logging.getLogger(__name__)

class TelegramCommand(models.Model):
    """
        Schedule required to run multiple commands
    """
    _inherit = "telegram.command"

    hide = fields.Boolean('Hide from /help', default=False,
                             help='Hide from /help command list')

    @api.model
    def action_handle_subscriptions(self, ids=None):
        """
        Odoo Telegram did not support multiple arguments
        :param ids: list of telegram command id
        :return:
        """
        for id in ids:
            super(TelegramCommand, self).action_handle_subscriptions(id)
        return True

