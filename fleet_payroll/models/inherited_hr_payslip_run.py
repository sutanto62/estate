# -*- coding: utf-8 -*-

import logging
from openerp import models, fields, api, exceptions, _
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

_logger = logging.getLogger(__name__)

class FleetPayslipRun(models.Model):

    inherit='hr.payslip.run'

