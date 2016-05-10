from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar


# class MasterTimesheet(models.Model):
#
#     _name = 'estate.timesheet'
#     _description = "Estate Master Time Sheet for Activity"

class TimesheetActivityTransport(models.Model):

    _name = 'estate.timesheet.activity.transport'
    _description = "Estate Master Time Sheet for Activity Transport"

    name=fields.Char("Timesheet Activity Tranport")
    date_activity_transport = fields.Date("Date activity Transport")
    seeddo_id = fields.Many2one('estate.nursery.seeddo')
    employee_id = fields.Many2one('hr.employee','Employee ID')
    vehicle_id = fields.Many2one('fleet.vehicle')
    activity_id = fields.Many2one('estate.activity')
    partner_id=fields.Many2one('res.partner')
    timesheet_activity_code = fields.Char()
    start_location = fields.Many2one('estate.block.template')
    end_location = fields.Many2one('estate.block.template')
    distance_location = fields.Float('Distance Location')
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    total_time = fields.Datetime()
    comment = fields.Text()
    state=fields.Selection([('draft','Draft'),
        ('confirmed', 'Confirmed'),('approved1','First Approval'),('approved2','Second Approval'),
        ('done', 'Done')],string="Activity Timesheet State")

    #Sequence Recovery code
    # def create(self, cr, uid, vals, context=None):
    #     vals['timesheet_activity_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.timesheet.activity.transport')
    #     res=super(TimesheetActivityTransport, self).create(cr, uid, vals)
    #     return res

     #state for Cleaving
    @api.one
    def action_draft(self):
        """Set Selection State to Draft."""
        self.state = 'draft'

    @api.one
    def action_confirmed(self):
        """Set Selection state to Confirmed."""
        self.state = 'confirmed'

    @api.one
    def action_approved1(self):
        """Set Selection state to Confirmed."""
        self.state = 'approved1'

    @api.one
    def action_approved2(self):
        """Set Selection state to Confirmed."""
        self.state = 'approved2'

    @api.one
    def action_approved(self):
        """Approved Selection is planted Seed to batch."""
        # self.action_receive()
        self.state = 'done'

    # @api.one
    # def action_receive(self):
    #     self.action_move()
    #
    # @api.one
    # def action_move(self):


class MasterPath(models.Model):

    _name = 'path.location'
    _description = "Estate Master path location"

    name=fields.Char("Master Path")
    distance_location = fields.Float('Distance Location',digits=(2,2))
    path_price = fields.Float('Standard Price',digits=(2,2))
    start_location=fields.Many2one('estate.block.template', "Plot")
    end_location=fields.Many2one('estate.block.template', "Plot")
    comment = fields.Text()

    # #ochange field
    # @api.multi
    # @api.onchange('type')
    # def _onchange_location(self):
    #     if self:
    #         if type == 'mn' :
    #             arrLocation=[]
    #             arrEndLocation=[]
    #             startlocbatch = self.env['estate.nursery.batchline'].search([]).location_id.id
    #             print "testlocation"
    #             print startlocbatch
    #             endlocbatch = self.env['estate.block.template'].search([('estate_location', '=', True),
    #                                           ('estate_location_level', '=', '3'),
    #                                           ('estate_location_type', '=', 'nursery'),
    #                                           ('stage_id','=',4),
    #                                           ('scrap_location', '=', False)]).id
    #             print "testlocation"
    #             print endlocbatch
    #             for a in startlocbatch:
    #                 arrLocation.append(a.id)
    #                 print arrLocation
    #             for b in endlocbatch :
    #                 arrEndLocation.append(b.id)
    #                 print arrEndLocation
    #             return {'domain' : {
    #                             'start_location': [('id','=',arrLocation)],
    #                             'end_location' :[('id','=',arrEndLocation)]
    #
    #                 }
    #             }
    #         if type == 'tp' :
    #             arrLocation=[]
    #             arrEndLocation=[]
    #             startlocbatch = self.env['estate.block.template'].search([('estate_location', '=', True),
    #                                           ('estate_location_level', '=', '3'),
    #                                           ('estate_location_type', '=', 'nursery'),
    #                                           ('stage_id','=',4),
    #                                           ('scrap_location', '=', False)]).id
    #             endlocbatch = self.env['estate.block.template'].search([('estate_location', '=', True),
    #                                                   ('estate_location_level', '=', '3'),
    #                                                   ('estate_location_type', '=', 'planted'),
    #                                                   ('scrap_location', '=', False)]).id
    #             for a in startlocbatch:
    #                 arrLocation.append(a.id)
    #             for b in endlocbatch :
    #                 arrEndLocation.append(b.id)
    #             return {'domain' : {
    #                             'start_location': [('id','=',arrLocation)],
    #                             'end_location' :[('id','=',arrEndLocation)]
    #
    #                 }
    #             }