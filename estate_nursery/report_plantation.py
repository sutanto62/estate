from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar


class ReportPlantation(models.Model):
    _inherit = "estate.nursery.selection"

    reportline_id= fields.Many2one("estate.nursery.reportline",
                                   default=lambda self: self.reportline_id.search([('name','=','Report Pre Nursery')]))
class ReportplanBatch(models.Model):
    _inherit = "estate.nursery.batch"

    reportline_id= fields.Many2one("estate.nursery.reportline",
                                   default=lambda self: self.reportline_id.search([('name','=','Report Pre Nursery')]))


class ReportLine(models.Model):
    _name = "estate.nursery.reportline"

    name=fields.Char("Report Plantation Name ")
    partner_id=fields.Many2one("res.partner")
    report_date = fields.Datetime("Report Date",compute="_report_date",readonly=True)
    batch_ids = fields.One2many("estate.nursery.batch","reportline_id","selection")
    selection_ids = fields.One2many("estate.nursery.selection","reportline_id","selection")
    kebun_location_id = fields.Many2one('stock.location',"Estate Location",
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '1'),
                                                  ],
                                        default=lambda self: self.kebun_location_id.search([('name','=','Liyodu Estate')]))

    #datetime

    @api.one
    @api.depends("report_date")
    def _report_date(self):
        today = datetime.now()
        self.report_date=today

