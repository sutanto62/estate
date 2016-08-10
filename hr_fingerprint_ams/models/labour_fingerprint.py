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
    _description = 'Compare number of day with fingerprint.'
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

    def init(self, cr):
        """ Initialize tablefunc module
            The tablefunc module includes various functions that return tables (that is, multiple rows).
            These functions are useful both in their own right and as examples of how to write C functions
            that return multiple rows.
            """
        cr.execute("""
                SELECT
                    extname
                FROM
                    pg_extension
                WHERE
                    extname='tablefunc';
            """)
        check = cr.fetchone()
        if check:
            return {}
        try:
            cr.execute("""
                CREATE EXTENSION tablefunc;
            """)
        except Exception:
            raise MissingError(
                "Error, can not automatically initialize tablefunc support. "
                "Database user may have to be superuser and postgres/postgis "
                "extentions with their devel header have to be installed. "
                "If you do not want Odoo to connect with a super user "
                "you can manually prepare your database. To do this"
                "open a client to your database using a super user and run: \n"
                "CREATE EXTENSION tablefunc;\n"
            )

        cr.execute("""
            CREATE OR REPLACE FUNCTION total_number_of_day (employee_id int, upkeep_date date)
            RETURNS decimal AS $total$
            declare
                total decimal ;
            BEGIN
               SELECT sum(l.number_of_day) into total FROM estate_upkeep_labour l
               WHERE l.employee_id = $1 AND l.upkeep_date = $2;
               RETURN total;
            END;
            $total$ LANGUAGE plpgsql;
        """)

        tools.drop_view_if_exists(cr, 'hr_fingerprint_ams_fingerprint')
        cr.execute("""
            CREATE or REPLACE VIEW hr_fingerprint_ams_fingerprint
            as
            SELECT
                row_number() over (order by ct.row_name) as id,
                ct.row_name as name,
                substring(ct.row_name from position('/'  in ct.row_name)+1 for char_length(ct.row_name))::date as date,
                ct.sign_in,
                ct.sign_out,
                ee.id as employee_id,
                tm.id as team_id,
                t.assistant_id,
                (date_part('hour', ct.sign_out - ct.sign_in)+(date_part('minute', ct.sign_out - ct.sign_in)/60)::numeric(4,2)) as worked_hours,
                total_number_of_day(
                    substring(ct.row_name from 1 for position('/' in ct.row_name)-1)::int,
                    substring(ct.row_name from position('/' in ct.row_name)+1 for char_length(ct.row_name))::date
                ) as number_of_day
            FROM crosstab(
                $$
                SELECT a.row_name, /* a.name_related, a.upkeep_date, a.hk, */ b.action::text, b.name FROM (
                    SELECT
                        concat(l.employee_id,'/', l.upkeep_date) as row_name,
                        l.upkeep_date,
                        e.name_related,
                        sum(l.number_of_day) as hk
                    FROM estate_upkeep_labour l
                    LEFT JOIN hr_employee e on l.employee_id = e.id
                    WHERE
                        l.number_of_day > 0
                    GROUP BY l.employee_id, l.upkeep_date, e.name_related
                ) a
                LEFT JOIN (
                    SELECT
                        concat(ee.id, '/', fa.date) as row_name,
                        ha.action,
                        ha.name,
                        ha.worked_hours
                    FROM hr_fingerprint_ams_attendance fa
                    LEFT JOIN hr_employee ee on lower(fa.employee_name) = lower(ee.name_related)
                    LEFT JOIN hr_attendance ha on ha.finger_attendance_id = fa.id
                ) b on a.row_name = b.row_name
                ORDER BY a.name_related, a.upkeep_date, b.name;
                $$
                ) as ct(row_name text, sign_in timestamp, sign_out timestamp)
            LEFT JOIN hr_employee ee on substring(ct.row_name from 1 for position('/' in ct.row_name)-1)::int = ee.id
            LEFT JOIN estate_hr_member tm on tm.employee_id = ee.id
            LEFT JOIN estate_hr_team t on tm.team_id = t.id
            ;
            """
        )
