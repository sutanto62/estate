from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar


class ReportPlantation(models.Model):
    _inherit = "estate.nursery.batch"

    reportline_id= fields.Many2one("estate.nursery.reportline")

class ReportLine(models.Model):
    _name = "estate.nursery.reportline"

    name=fields.Char("Report Plantation Name ")
    report_date = fields.Datetime("Report Date",compute="_report_date",readonly=True)
    batch_ids = fields.One2many("estate.nursery.batch","reportline_id","batchs")
    #datetime

    @api.one
    @api.depends("report_date")
    def _report_date(self):
        today = datetime.now()
        self.report_date=today