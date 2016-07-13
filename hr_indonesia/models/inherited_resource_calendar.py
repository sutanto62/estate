# -*- coding: utf-8 -*-

from openerp import models, fields

class ResourceCalendar(models.Model):
    """ Extend resource.calendar to support Estate Business Process
    """
    _inherit = 'resource.calendar'

    condition_ids = fields.One2many('hr_indonesia.calendar_condition', 'resource_calendar_id', 'Calendar Condition')

class Condition(models.Model):
    """
    Support mandatory early in and late out
    """
    _name = 'hr_indonesia.calendar_condition'
    _description = 'HR Indonesia Calendar Condition'

    resource_calendar_id = fields.Many2one('resource.calendar', 'Resource Calendar')
    name = fields.Char('Condition')
    time = fields.Float('Time', help='* negative value, early-in'\
                                     '* positive value, late-out.')
    type = fields.Selection([('in', 'Mandatory Early In'),
                             ('out', 'Mandatory Early Out'),
                             ('optional', 'Optional In/Out')],
                            'Condition Type')