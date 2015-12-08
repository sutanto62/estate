from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar


class ReportPlantation(models.Model):
    _inherit = "estate.nursery.selection"

    reportline_id= fields.Many2one("estate.nursery.reportline",
                                   default=lambda self: self.reportline_id.search([('name','=','Report Pre Nursery')]))
class ReportPlantationline(models.Model):
    _inherit = "estate.nursery.selectionline"

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
    cause_id=fields.Many2one("estate.nursery.cause")
    report_date = fields.Datetime("Report Date",compute="_report_date",readonly=True)
    batch_ids = fields.One2many("estate.nursery.batch","reportline_id","selection")
    selection_ids = fields.One2many("estate.nursery.selection","reportline_id","selection")
    selectionline_ids = fields.One2many("estate.nursery.selectionline","reportline_id","selection")
    total_do = fields.Integer("Total DO",store=True,compute="_get_total")
    total_planted = fields.Integer("Total planted",store=True,compute="_get_total_planted")
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

    #total DO
    @api.one
    @api.depends("total_do")

    def _get_total(self):
        batchids = self.batch_ids
        total_do = self.total_do
        for item in batchids:
            total_do += item.qty_received
            print total_do

    #total planted
    @api.one
    @api.depends("total_planted","batch_ids")

    def _get_total_planted(self):
        batch_ids = self.batch_ids
        total_planted = self.total_planted
        for item in batch_ids:
            total_planted += item.qty_planted
            print total_planted


