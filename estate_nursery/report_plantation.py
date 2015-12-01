from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar


class ReportPlantation(models.Model):
    _inherit = "estate.nursery.selection"

    reportline_id= fields.Many2one("estate.nursery.reportline")
class ReportPlan(models.Model):
    _inherit = "estate.nursery.selectionline"

    reportline_id=fields.Many2one("estate.nursery.reportline")

class ReportLine(models.Model):
    _name = "estate.nursery.reportline"

    name=fields.Char("Report Plantation Name ")
    partner_id=fields.Many2one("res.partner")
    report_date = fields.Datetime("Report Date",compute="_report_date",readonly=True)
    selectionline_ids = fields.One2many("estate.nursery.selectionline","reportline_id","selection")
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

class particularreport(models.AbstractModel):

     _name = "report.module.reportline"

     @api.multi

     def render_html(self, data=None):

        report_obj = self.env['report']
        report = report_obj._get_report_from_name('estate_nursery.report_name')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': ReportLine.model,
            'docs': self,

        }
        return report_obj.render('estate.nursery.report_name', docargs)
