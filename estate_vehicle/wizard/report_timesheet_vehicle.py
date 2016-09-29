
from openerp import models, fields, api
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _

class ReportTimesheetVehicle(models.TransientModel):
    _name = "wizard.report.timesheet.vehicle"
    _inherit = "report.common.vehicle"
    _description = "Vehicle Report"

    def _print_report(self, data):
        return self.env['report'].with_context(landscape=True).get_action(self, 'estate_vehicle.report.common.vehicle', data=data)