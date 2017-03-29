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
            select
                row_number() over (order by concat(a.employee_id,'/',a.upkeep_date)) as id,
                concat(a.employee_id,'/',a.upkeep_date) as name,
                a.employee_id,
                a.upkeep_date as date,
                c.name as sign_in,
                d.name as sign_out,
                a.upkeep_team_id as team_id,
                b.employee_id as assistant_id,
                (date_part('hour', d.name - c.name)+(date_part('minute', d.name - c.name)/60)::numeric(4,2)) as worked_hours,
                f.number_of_day,
                CASE WHEN c.state isnull THEN 'attendance'
                    ELSE c.state
                        END
                from estate_upkeep_labour a
                join estate_hr_team b on a.upkeep_team_id = b.id
                left outer join (
                    select
                        concat(cc.employee_id,'/', cc.name::date),
                        cc.employee_id,
                        cc.name,
                        cc.state
                    from hr_attendance cc
                        where cc.action = 'sign_in'
                    ) c on concat(a.employee_id,'/', (a.upkeep_date at time zone 'UTC')::date) = concat(c.employee_id,'/', c.name::date) -- convert to utc
                left outer join (
                    select
                        dd.employee_id,
                        dd.name
                    from hr_attendance dd
                        where dd.action = 'sign_out'
                    ) d on concat(a.employee_id,'/', a.upkeep_date) = concat(d.employee_id,'/', d.name::date)  -- do not convert to utc
                left outer join (
                    select ff.employee_id, ff.upkeep_date, sum(ff.number_of_day) as number_of_day
                    from estate_upkeep_labour ff
                    group by ff.employee_id, ff.upkeep_date
                    ) f on ((f.employee_id = a.employee_id) AND (f.upkeep_date = a.upkeep_date))
                group by a.employee_id, a.upkeep_date, c.name, d.name, a.upkeep_team_id, b.employee_id, f.number_of_day, c.state
                order by concat(a.employee_id,'/',a.upkeep_date);
            """
        )