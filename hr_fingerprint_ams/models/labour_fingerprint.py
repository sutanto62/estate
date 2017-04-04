# -*- coding: utf-8 -*-

from openerp import models, fields, tools
from openerp.exceptions import MissingError


class LabourFingerprint(models.Model):
    """
    Control fingerprint over claimed work day at upkeep.
    Note:
    - Do not try to join with estate upkeep labour to get division.
    """
    _name = 'hr_fingerprint_ams.fingerprint'
    _description = 'Labour Fingerprint'
    _auto = False

    name = fields.Char('Row Name', help='Employee ID and Upkeep Date')
    date = fields.Date('Date')
    sign_in = fields.Datetime('Sign In')
    sign_out = fields.Datetime('Sign Out')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    team_id = fields.Many2one('estate.hr.team', 'Team')
    assistant_id = fields.Many2one('hr.employee', 'Assistant')
    company_id = fields.Many2one('res.company', 'Company')
    estate_id = fields.Many2one('stock.location', "Estate",
                                domain=[('estate_location', '=', True), ('estate_location_level', '=', '1'),
                                        ('estate_location_type', '=', 'planted')])
    division_id = fields.Many2one('stock.location', "Division",
                                  domain=[('estate_location', '=', True), ('estate_location_level', '=', '2')])
    worked_hours = fields.Float('Worked Hours', help='Included time rest')
    number_of_day = fields.Float('Number of Days')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('approved', 'Approved'),
                              ('correction', 'Correction'),
                              ('payslip', 'Payslip'),
                              ('attendance', 'No Attendance Created')],
                             string='State',
                             help='Fingerprint state.')

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'hr_fingerprint_ams_fingerprint')
        cr.execute(
            """
            CREATE or REPLACE VIEW hr_fingerprint_ams_fingerprint
            as
            SELECT row_number() OVER (ORDER BY concat(a.employee_id, '/', a.upkeep_date)) AS id,
            concat(a.employee_id, '/', a.upkeep_date) AS name,
            a.employee_id,
            a.upkeep_date AS date,
            c.name AS sign_in,
            d.name AS sign_out,
            a.upkeep_team_id AS team_id,
            b.assistant_id,
            a.estate_id,
            a.division_id,
            a.company_id,
            date_part('hour'::text, d.name - c.name) + (date_part('minute'::text, d.name - c.name) / 60::double precision)::numeric(4,2)::double precision AS worked_hours,
            f.number_of_day,
                    CASE
                        WHEN c.state IS NULL THEN 'attendance'::character varying
                        ELSE c.state
                    END AS state
               FROM estate_upkeep_labour a
                 JOIN estate_hr_team b ON a.upkeep_team_id = b.id
                 LEFT JOIN ( SELECT concat(cc.employee_id, '/', cc.name::date) AS concat,
                        cc.employee_id,
                        cc.name,
                        cc.state
                       FROM hr_attendance cc
                      WHERE cc.action::text = 'sign_in'::text) c ON concat(a.employee_id, '/', timezone('UTC'::text, a.upkeep_date::timestamp with time zone)::date) = concat(c.employee_id, '/', c.name::date)
                 LEFT JOIN ( SELECT dd.employee_id,
                        dd.name
                       FROM hr_attendance dd
                      WHERE dd.action::text = 'sign_out'::text) d ON concat(a.employee_id, '/', a.upkeep_date) = concat(d.employee_id, '/', d.name::date)
                 LEFT JOIN ( SELECT ff.employee_id,
                        ff.upkeep_date,
                        sum(ff.number_of_day) AS number_of_day
                       FROM estate_upkeep_labour ff
                      GROUP BY ff.employee_id, ff.upkeep_date) f ON f.employee_id = a.employee_id AND f.upkeep_date = a.upkeep_date
              GROUP BY a.employee_id, a.upkeep_date, c.name, d.name, a.upkeep_team_id, b.assistant_id,
                a.estate_id, a.company_id, a.division_id, f.number_of_day, c.state
              ORDER BY concat(a.employee_id, '/', a.upkeep_date);
            """
        )