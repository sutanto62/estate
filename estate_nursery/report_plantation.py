from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar


class ReportPlantation(models.Model):

    _name = 'estate.nursery.reportplantation'

    names=fields.Char("Report Plantation Name ")
    report_date = fields.Datetime("Report Date",compute="_report_date",readonly=True)
    partner_id = fields.Many2one('res.partner')
    batch_ids = fields.One2many('estate.nursery.batch', 'reportplan_id', "Report Lines")
    selection_ids = fields.One2many('estate.nursery.selection', 'reportplan_id',"Report Lines")

    #datetime
    @api.one
    @api.depends("report_date")
    def _report_date(self):
        today = datetime.now()
        self.report_date=today