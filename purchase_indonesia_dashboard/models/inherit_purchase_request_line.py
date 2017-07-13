from openerp import models, fields, api, exceptions
from openerp.exceptions import ValidationError
from datetime import datetime, date
from dateutil.relativedelta import *

class InheritPurchaseRequestLine(models.Model):

    _inherit = 'purchase.request.line'

    location = fields.Char('Location',related="request_id.type_location",store=True)
    type_purchase = fields.Many2one('purchase.indonesia.type','Purchase Type',related="request_id.type_purchase",store=True)