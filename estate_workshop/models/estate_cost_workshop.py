from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal


class ViewTotalAmountTimesheetMecanic(models.Model):

    _name = 'view.timesheet.mecanic.amounttotal'
    _description = " summary cost for vehicle"
    _auto = False
    _order='employee_id'

    id = fields.Integer()
    employee_id = fields.Many2one('hr.employee')
    total_time_per_day = fields.Float()
    hourly_wage = fields.Float()
    daily_wage = fields.Float()
    hour = fields.Float()
    total_amount = fields.Float()

    def init(self, cr):
        cr.execute("""create or replace view view_timesheet_mecanic_amounttotal as
        select parent_id as id,employee_id,
               total_time_per_day,
               hourly_wage,
               daily_wage,
               hour,
               CASE
                WHEN total_time_per_day < hour THEN (total_time_per_day*hourly_wage)
                WHEN total_time_per_day >= hour THEN (daily_wage)
                END total_amount from (
        select (month_log::text||year_log::text||asset::text)::Integer parent_id,employee_id,sum(total_time) as total_time_per_day,hourly_wage,daily_wage,day,hour from(
        select
            date_part('month', create_date) month_log,
            date_part('year', create_date) year_log,
            employee_id,
            asset,
            create_date,
            c.mastertask_id,
            activity_id,
            start_time,
            end_time ,
            (end_time-start_time) as total_time,
            wage,
            weekly_wage,
            daily_wage,
            hourly_wage,
            day,
            hour
            from (
            select
                asset_id as asset,
                create_date,
                mastertask_id,employee_id,activity_id,start_time,end_time
                from estate_mecanic_timesheet mt
                inner join (
                select
                    id,
                    employee_id,
                    activity_id,
                    start_time,
                    end_time
                from estate_timesheet_activity_transport)etat on mt.timesheet_id=etat.id
                )c
                left join (
                select
                    hre.id,
                    wage,
                    weekly_wage,
                    daily_wage,
                    hourly_wage,
                    day,
                    hour from hr_employee hre right join hr_contract hrc on hre.id=hrc.employee_id
                )hrcon on c.employee_id = hrcon.id
                )b group by employee_id , day, hour,hourly_wage,daily_wage,month_log,year_log,asset)a""")