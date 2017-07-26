# -*- coding: utf-8 -*-

from openerp import models, fields, tools, api
from openerp.exceptions import MissingError
import openerp.addons.decimal_precision as dp

# todo change to UpkeepFingerprint
class LaborFingerprint(models.Model):
    """
    Deprecated - high cost postgres - use UpkeepFingerprint in the future
    Control fingerprint over claimed work day at upkeep.
    Note:
    - Do not try to join with estate upkeep labour to get division.
    """
    _name = 'hr_fingerprint_ams.fingerprint'
    _description = 'Labor Fingerprint'
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
        tools.drop_view_if_exists(cr, 'public.hr_fingerprint_ams_fingerprint')
        cr.execute(
            """
            CREATE or REPLACE VIEW public.hr_fingerprint_ams_fingerprint
            as
            SELECT 
                row_number() OVER (ORDER BY concat(a.employee_id, '/', a.upkeep_date)) AS id,
                concat(a.employee_id, '/', a.upkeep_date) AS name,
                a.employee_id,
                a.upkeep_date AS date,
                c.name AS sign_in,
                d.name AS sign_out,
                a.upkeep_team_id AS team_id,
                b.assistant_id,
                a.estate_id,
                a.division_id,
                a.employee_company_id company_id,
                (date_part('hour'::text, (d.name - c.name)) + (((date_part('minute'::text, (d.name - c.name)) / (60)::double precision))::numeric(4,2))::double precision) AS worked_hours,
                f.number_of_day,
                    CASE
                        WHEN (((c.name IS NULL) AND (d.name IS NULL)) AND (g.name IS NULL)) THEN 'attendance'::character varying
                        ELSE 'approved'::character varying
                    END AS state
               FROM (((((estate_upkeep_labour a
                 JOIN estate_hr_team b ON ((a.upkeep_team_id = b.id)))
                 LEFT JOIN ( SELECT concat(cc.employee_id, '/', (cc.name)::date) AS concat,
                        cc.employee_id,
                        cc.name,
                        cc.state
                       FROM hr_attendance cc
                      WHERE ((cc.action)::text = 'sign_in'::text)) c ON ((concat(a.employee_id, '/', a.upkeep_date) = concat(c.employee_id, '/', c.name::date))))
                 LEFT JOIN ( SELECT dd.employee_id,
                        dd.name,
                        dd.state
                       FROM hr_attendance dd
                      WHERE ((dd.action)::text = 'sign_out'::text)) d ON ((concat(a.employee_id, '/', a.upkeep_date) = concat(d.employee_id, '/', d.name::date))))
                 LEFT JOIN ( SELECT ff.employee_id,
                        ff.upkeep_date,
                        sum(ff.number_of_day) AS number_of_day
                       FROM estate_upkeep_labour ff
                      GROUP BY ff.employee_id, ff.upkeep_date) f ON (((f.employee_id = a.employee_id) AND (f.upkeep_date = a.upkeep_date))))
                 LEFT JOIN ( SELECT gg.employee_id,
                        gg.name,
                        gg.state
                       FROM hr_attendance gg
                      WHERE ((gg.action)::text = 'action'::text)) g ON ((concat(a.employee_id, '/', a.upkeep_date) = concat(g.employee_id, '/', g.name::date))))
              GROUP BY a.employee_id, a.upkeep_date, c.name, d.name, g.name, a.upkeep_team_id, b.assistant_id, a.estate_id, a.employee_company_id, a.division_id, f.number_of_day, c.state
              ORDER BY concat(a.employee_id, '/', a.upkeep_date);
            """
        )


class UpkeepFingerprint(models.Model):
    """
    Model to compare upkeep number of day with attendance number of day.
    Remark: use hr_attendance help - online form for exception.
    """
    _name = 'hr_fingerprint_ams.upfingerprint'
    _auto = False
    _description = 'Upkeep Fingerprint'

    name = fields.Char('Name', compute='_compute_name')
    employee_company_id = fields.Many2one('res.company', 'Company',
                                          help='Registered employee company.')
    assistant_id = fields.Many2one('hr.employee', 'Team Assistant',
                                   help='Assistant of team.')
    team_id = fields.Many2one('estate.hr.team', 'Team',
                              help='Estate team.')
    division_id = fields.Many2one(related='team_id.division_id', store=True,
                                  help='Division of team.')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    nik_number = fields.Char('Employee Identity Number')
    contract_type = fields.Selection(related='employee_id.contract_type', store=True)
    contract_period = fields.Selection(related='employee_id.contract_period', store=True)
    upkeep_date = fields.Date('Upkeep Date')
    number_of_day = fields.Float('Number Of Day', digits=dp.get_precision('Fingerprint'))
    attendance_date = fields.Date('Fingerprint Date')
    attendance_time = fields.Char('Fingerprint Time')
    fingerprint = fields.Char('Fingerprint Action')
    action_reason_id = fields.Many2one('hr.action.reason', 'Reason')
    worked_hours = fields.Float('Fingerprint Worked Hours', digits=dp.get_precision('Fingerprint Time'))
    # finger_attendance_id = fields.Many2one('hr_fingerprint_ams.attendance', 'Fingerprint Attendance')
    number_of_day_fingerprint = fields.Integer('Fingerprint')
    delta = fields.Float('Without Fingerprint', digits=dp.get_precision('Fingerprint'))
    # work_schedules = fields.Char(related='finger_attendance_id.work_schedules')

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'public.hr_fingerprint_ams_upfingerprint')
        cr.execute(
            """
            CREATE or REPLACE VIEW public.hr_fingerprint_ams_upfingerprint
            as
            select
                row_number() OVER (ORDER BY concat(a.employee_id, '/', a.upkeep_date)) AS id,
                a.employee_company_id "employee_company_id",
                e.assistant_id "assistant_id",
                a.upkeep_team_id "team_id",  -- salah (kemandoran khl)
                e.division_id "division_id",
                a.employee_id "employee_id",
                b.nik_number "nik_number",
                b.contract_type "contract_type",
                b.contract_period "contract_period",
                a.upkeep_date "upkeep_date",
                max( a.number_of_day ) "number_of_day",
                c.attendance_date "attendance_date",
                c.attendance_time "attendance_time",
                c.fingerprint,
                c.action_reason "action_reason_id",
                c.worked_hours,
                case
                    when c.worked_hours > 0 then 1
                    else 0
                end "number_of_day_fingerprint",
                (
                    abs( sum( a.number_of_day )- case when c.worked_hours > 0 then 1 else 0 end )+(
                        sum( a.number_of_day )- case
                            when c.worked_hours > 0 then 1
                            else 0
                        end
                    )
                )/ 2 "delta"
            from
                estate_upkeep_labour a 
                inner join hr_employee b on b.id = a.employee_id 
                left join(
                    select
                        employee_id,
                        name::date "attendance_date",
                        string_agg(
                            (
                                name::time
                            )::text,
                            ','
                        order by
                            name
                        ) "attendance_time",
                        string_agg(
                            action::text,
                            ','
                        order by
                            action
                        ) "fingerprint",
                        action_desc "action_reason",
                        sum( worked_hours ) "worked_hours"
                    from
                        hr_attendance
                    where
                        employee_id in(
                            select
                                id
                            from
                                hr_employee
                            where
                                contract_period = '2'
                        )
                    group by
                        1,
                        2,
                        5
                    order by
                        1,
                        2,
                        3
                ) c on c.employee_id = a.employee_id
                and(
                    c.attendance_date = a.upkeep_date
                )
                left join estate_hr_team e on e.id = a.upkeep_team_id
            where
                b.contract_period = '2'
            group by
                a.employee_company_id,
                e.assistant_id,
                a.upkeep_team_id,
                e.division_id,
                a.employee_id,
                b.nik_number,
                b.contract_type,
                b.contract_period,
                a.upkeep_date,
                c.attendance_date,
                c.attendance_time,
                c.fingerprint,
                c.action_reason,
                c.worked_hours
            order by
                1,
                2,
                3,
                4,
                5,
                9;
            """
        )

    @api.multi
    def _compute_name(self):
        self.ensure_one()
        res = self.employee_id.name_related + ' ' + self.upkeep_date
        self.name = res
        return res