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
                                   select
                                        row_number() over()id,
                                        date,mo_id,
                                        sum(amount) total_amount,
                                        month_log,year_log,vehicle_id from (
                                        select
                                            create_date date,
                                            (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id,
                                            month_log,
                                            year_log,vehicle_id,
                                            total_time ,
                                            mo_id,
                                            wage,
                                            total_hour_per_day,total_hour_per_week,
                                            contract_type,
                                            contract_period,
                                            case
                                            when contract_type = '1' and contract_period = '2'
                                                then
                                                    case when total_time < total_hour_per_day
                                                        then
                                                            round(((wage /(total_hour_per_week))/total_hour_per_day)*total_time)
                                                        when total_time >= total_hour_per_day
                                                        then
                                                            round((wage /(total_hour_per_week))/total_hour_per_day)
                                                    end
                                            when contract_type = '1' and contract_period = '1'
                                                    then
                                                    case
                                                        when total_time < (total_hour_per_week*4)
                                                            then
                                                                round((((wage /(total_hour_per_week))/total_hour_per_day))*total_time)
                                                        when total_time >= (total_hour_per_week*4)
                                                            then
                                                                round((wage /(total_hour_per_week))/total_hour_per_day)
                                                    end
                                            when contract_type = '2' and contract_period = '1'
                                                then
                                                    case
                                                        when total_time >= (total_hour_per_week*4)
                                                            then
                                                                round((wage /(total_hour_per_week))/total_hour_per_day)
                                                        else
                                                            round(((wage /(total_hour_per_week))/total_hour_per_day)*total_time)
                                                            end
                                            when contract_type = '2' and contract_period = '2'
                                                then
                                                    case
                                                        when total_time < total_hour_per_day
                                                            then
                                                                round(((wage /(total_hour_per_week))/total_hour_per_day)*total_time)
                                                         when total_time >= total_hour_per_day
                                                            then
                                                                round((wage /(total_hour_per_week))/total_hour_per_day)
                                                    end
                                            end amount
                                            from(
                                                select
                                                    create_date::Date,
                                                    date_part('month', create_date) month_log,
                                                    date_part('year', create_date) year_log,
                                                    vehicle_id,
                                                    asset_id asset,
                                                    mo_id,
                                                    mastertask_id,
                                                    etat.employee_id employee_id,
                                                    activity_id,start_time,end_time,
                                                    wage,total_hour_per_day,total_hour_per_week,
                                                    contract_type,
                                                    contract_period,
                                                    sum(end_time-start_time) as total_time
                                                    from estate_mecanic_timesheet mt
                                                    left join (
                                                        select
                                                            mo.id as mo_id,
                                                            et_id,
                                                            employee_id,
                                                            activity_id,
                                                            start_time,
                                                            end_time,
                                                            vehicle_id from mro_order mo
                                                            left join(
                                                                select
                                                                    et.id as et_id,
                                                                    employee_id,
                                                                    activity_id,
                                                                    start_time,
                                                                    end_time,owner_id,vehicle_id,dc_type
                                                                from estate_timesheet_activity_transport et where dc_type is not null
                                                                )moa on mo.id = moa.owner_id
                                                                    group by mo_id,et_id,employee_id,activity_id,start_time,end_time,vehicle_id
                                                                )etat on mt.timesheet_id=etat.et_id
                                                    left join (
                                                    select
                                                        employee_id,
                                                        wage ,
                                                        total_hour_per_day,(total_hour_per_day * 5) total_hour_per_week,
                                                        contract_type,
                                                        contract_period from hr_employee hre
                                                        left join hr_contract hrc on hre.id = hrc.employee_id
                                                        inner join (
                                                            select
                                                                rc_id,
                                                                dayofweek,
                                                                sum(hour_work) as total_hour_per_day from (
                                                            select
                                                                rc_id,
                                                                nameday,
                                                                count(dayofweek)"day",
                                                                dayofweek,
                                                                hour_work from (
                                                            select *,
                                                                rc.id rc_id,
                                                                rca.name as nameday,
                                                                (hour_to - hour_from) hour_work from  resource_calendar rc
                                                                left join resource_calendar_attendance rca on rc.id = rca.calendar_id
                                                                group by dayofweek,rc.id,rca.id order by dayofweek
                                                        )a group by
                                                            hour_to,
                                                            hour_from,
                                                            nameday,
                                                            rc_id,
                                                            dayofweek,
                                                            hour_work order by nameday asc)b
                                                            group by rc_id,dayofweek
                                                    )a on hrc.working_hours = a.rc_id group by employee_id , wage,total_hour_per_day,contract_type, contract_period
                                                    )b on b.employee_id = etat.employee_id group by create_date,vehicle_id,
                                                    asset,
                                                    mo_id,
                                                    mastertask_id,
                                                    etat.employee_id,activity_id,start_time,end_time,
                                                    wage,total_hour_per_day,total_hour_per_week,
                                                    contract_type,
                                                    contract_period
                                            )c
                                            )d group by mo_id,date,month_log,year_log,vehicle_id""")


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


