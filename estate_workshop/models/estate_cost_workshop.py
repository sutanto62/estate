from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal


class ViewTotalAmountTimesheetMecanic(models.Model):

    _name = 'view.timesheet.mecanic.totalamounts'
    _description = " summary cost labour for mecanic "
    _auto = False
    _order='mo_id'

    id = fields.Integer()
    mo_id = fields.Integer()
    total_amount = fields.Float()
    year_log = fields.Char()
    month_log = fields.Char()
    vehicle_id = fields.Many2one('fleet.vehicle')

    def init(self, cr):
        cr.execute("""create or replace view view_timesheet_mecanic_totalamounts as
            select row_number() over()id,a.mo_id mo_id, sum(a.total_amount) total_amount,month_log,year_log,vehicle_id from (
                        select row_number() over()id,mo_id,
                               total_time_per_day,
                               hourly_wage,
                               daily_wage,count(*)"count",month_log,year_log,vehicle_id,
                               hour,
                               CASE
                                WHEN total_time_per_day < hour THEN (total_time_per_day*hourly_wage)
                                WHEN total_time_per_day >= hour THEN (daily_wage)
                                END total_amount from (
                        select (month_log::text||year_log::text||asset::text||mo_id::text)::Integer parent_id,mo_id,month_log,year_log,vehicle_id,
                        sum(total_time) as total_time_per_day,hourly_wage,daily_wage,day,hour from(
                        select
                            date_part('month', create_date) month_log,
                            date_part('year', create_date) year_log,
                            mo_id,asset,
                            vehicle_id,
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
                                vehicle_id,asset_id asset,
                                create_date,mo_id,
                                mastertask_id,employee_id,activity_id,start_time,end_time
                                from estate_mecanic_timesheet mt
                                left join (
                                select mo.id as mo_id,et_id,employee_id,activity_id,start_time,end_time,vehicle_id from mro_order mo left join(
                                select
                                    et.id as et_id,
                                    employee_id,
                                    activity_id,
                                    start_time,
                                    end_time,owner_id,vehicle_id,dc_type
                                from estate_timesheet_activity_transport et where dc_type is not null
                                )moa on mo.id = moa.owner_id group by mo_id,et_id,employee_id,activity_id,start_time,end_time,vehicle_id
                                )etat on mt.timesheet_id=etat.et_id
                                )c left join (
                                select
                                    hre.id,
                                    wage,
                                    weekly_wage,
                                    daily_wage,
                                    hourly_wage,
                                    day,
                                    hour from hr_employee hre right join hr_contract hrc on hre.id=hrc.employee_id where hre.job_id = 11
                                    )hrcon on c.employee_id = hrcon.id
                                    )b group by day, hour,hourly_wage,daily_wage,month_log,year_log,asset,vehicle_id,mo_id)a group by mo_id,total_time_per_day,
                               hourly_wage,
                               daily_wage,total_amount,
                               hour,month_log,year_log,vehicle_id
                        ) a group by a.mo_id,month_log,year_log,vehicle_id""")


class ViewTotalCostDetailWorkshopSparepart(models.Model):

    _name = 'view.cost.workshop.sparepart'
    _description = " summary cost sparepart workshop"
    _auto = False
    _order='mo_id'

    id = fields.Integer()
    mo_id = fields.Integer()
    parent_id = fields.Integer()
    total_amount = fields.Float()
    year_log = fields.Char()
    month_log = fields.Char()
    vehicle_id = fields.Many2one('fleet.vehicle')

    def init(self, cr):
        cr.execute("""create or replace view view_cost_workshop_sparepart as
                select row_number() over()id,mo_id, sum(total_cost) as total_amount,fleet_id as vehicle_id,month_log,year_log,parent_id from(
                select row_number() over()id,
                    (month_log::text||year_log::text||fleet_id::text)::Integer parent_id,
                    mo_id,
                    asset_id,fleet_id,month_log,year_log,
                    b.product_id,
                    qty_product,
                    cost ,
                    (qty_product*cost) as total_cost
                from(
                    select mo.id,fleet_id,date_part('day',mo.create_date) day_log,mo.id as mo_id,
                                        date_part('month',mo.create_date) month_log,
                                        date_part('year',mo.create_date) year_log
                                        ,asset_id,ewas.product_id,qty_product,cost
                                        from mro_order mo
                                      	inner join asset_asset aa on aa.id = mo.asset_id
                inner join (
                    select owner_id,product_id,qty_product,cost from estate_workshop_actual_sparepart ewas
                inner join (
                    select pp.id,cost from product_product pp
                inner join (
                    select pt.id,cost from product_template pt
                inner join (
                        select * from product_price_history)pph on pt.id=pph.product_template_id )a on a.id = pp.product_tmpl_id
                )c on ewas.product_id = c.id
                )ewas on mo.id = ewas.owner_id)b
                group by month_log,year_log,asset_id,mo_id,product_id,qty_product,cost,fleet_id,month_log,year_log)a
                group by mo_id,fleet_id,month_log,year_log,parent_id""")

class ViewCostTotalWorkshop(models.Model):

    _name = 'v.summary.cost.workshop.detail'
    _description = "summary cost per Maintenance Order Workshop"
    _auto = False
    _order='mo_id'

    id=fields.Integer()
    mo_id = fields.Integer()
    type_log = fields.Char()
    count = fields.Integer()
    total_amount =fields.Float()
    year_log = fields.Char()
    month_log = fields.Char()
    vehicle_id = fields.Many2one('fleet.vehicle')
    parent_id = fields.Many2one('v.summary.cost.vehicle')

    def init(self, cr):
        cr.execute("""create or replace view v_summary_cost_workshop_detail as
 	select detail.*, (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id from(
                select row_number() over()id,type_log,mo_id,"count",total_amount,year_log,month_log,vehicle_id from(
                select 'Cost Labour' as type_log,mo_id,count(*)"count",sum(total_amount) as total_amount,year_log,month_log,vehicle_id from(
                select * from view_timesheet_mecanic_totalamounts
                )cl group by mo_id,year_log,month_log,vehicle_id
            union
            select 'Cost Sparepart' as type_log,mo_id,count(*)"count",sum(total_amount) as total_amount,year_log,month_log,vehicle_id from(
            select * from view_cost_workshop_sparepart
                )cs group by mo_id,year_log,month_log,vehicle_id
                )utot)detail
            """)


