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
                                    total_time,
                                    mo_id,
                                    wage,
                                    total_hour_per_day,total_hour_per_week,
                                    contract_type,
                                    contract_period,
                                    case
                                    when contract_type = '1' and contract_period = '2' and date_end is null or date_end is not null and date_end > date_activity_transport
                                        then
                                            case when total_time < total_hour_per_day
                                                then
                                                    round(((wage /(total_hour_per_week))/total_hour_per_day)*total_time)
                                                when total_time >= total_hour_per_day
                                                then
                                                    round((wage /(total_hour_per_week))/total_hour_per_day)
                                            end
                                    when contract_type = '1' and contract_period = '1' and date_end is null or date_end is not null and date_end > date_activity_transport
                                            then
                                            case
                                                when total_time < (total_hour_per_week*4)
                                                    then
                                                        round((((wage /(total_hour_per_week))/total_hour_per_day))*total_time)
                                                when total_time >= (total_hour_per_week*4)
                                                    then
                                                        round((wage /(total_hour_per_week))/total_hour_per_day)
                                            end
                                    when contract_type = '2' and contract_period = '1' and date_end is null or date_end is not null and date_end > date_activity_transport
                                        then
                                            case
                                                when total_time >= (total_hour_per_week*4)
                                                    then
                                                        round((wage /(total_hour_per_week))/total_hour_per_day)
                                                else
                                                    round(((wage /(total_hour_per_week))/total_hour_per_day)*total_time)
                                                    end
                                    when contract_type = '2' and contract_period = '2' and date_end is null or date_end is not null and date_end > date_activity_transport
                                        then
                                            case
                                                when total_time < total_hour_per_day
                                                    then
                                                        round(((wage /(total_hour_per_week))/total_hour_per_day)*total_time)
                                                 when total_time >= total_hour_per_day
                                                    then
                                                        round((wage /(total_hour_per_week))/total_hour_per_day)
                                            end
                                     when contract_type = '1' and contract_period = '2' and date_end is not null and date_end <= date_activity_transport
                                        then
                                            case when total_time < total_hour_per_day
                                                then
                                                    0
                                                when total_time >= total_hour_per_day
                                                then
                                                  0
                                            end
                                    when contract_type = '1' and contract_period = '1' and date_end is not null and date_end <= date_activity_transport
                                            then
                                            case
                                                when total_time < (total_hour_per_week*4)
                                                    then
                                                        0
                                                when total_time >= (total_hour_per_week*4)
                                                    then
                                                        0
                                            end
                                    when contract_type = '2' and contract_period = '1' and date_end is not null and date_end <= date_activity_transport
                                        then
                                            case
                                                when total_time >= (total_hour_per_week*4)
                                                    then
                                                        0
                                                else
                                                    0
                                                    end
                                    when contract_type = '2' and contract_period = '2' and date_end is not null and date_end <= date_activity_transport
                                        then
                                            case
                                                when total_time < total_hour_per_day
                                                    then
                                                        0
                                                 when total_time >= total_hour_per_day
                                                    then
                                                        0
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
                                            case
                                                when date_end is null or date_end is not null and date_end > date_activity_transport
                                                    then wage
                                                when date_end is not null and date_end <= date_activity_transport
                                                    then 0
                                            end wage
                                            ,total_hour_per_day,total_hour_per_week,
                                            contract_type,
                                            contract_period,date_end,date_activity_transport,
                                            sum(end_time-start_time) as total_time
                                            from estate_mecanic_timesheet mt
                                            left join (
                                                select
                                                    mo.id as mo_id,
                                                    et_id,date_activity_transport,
                                                    employee_id,
                                                    activity_id,
                                                    start_time,
                                                    end_time,
                                                    vehicle_id from mro_order mo
                                                    left join(
                                                        select
                                                            et.id as et_id,
                                                            date_activity_transport,
                                                            employee_id,
                                                            activity_id,
                                                            start_time,
                                                            end_time,owner_id,vehicle_id,dc_type
                                                        from estate_timesheet_activity_transport et where dc_type is not null
                                                        )moa on mo.id = moa.owner_id
                                                            group by mo_id,et_id,employee_id,activity_id,start_time,end_time,vehicle_id,date_activity_transport
                                                        )etat on mt.timesheet_id=etat.et_id
                                            left join (
                                            select
                                                employee_id,
                                                wage,
                                                total_hour_per_day,(total_hour_per_day * 5) total_hour_per_week,
                                                contract_type,date_end,
                                                contract_period from hr_employee hre
                                                left join hr_contract hrc on hre.id = hrc.employee_id
                                                inner join (
                                                    select
                                                        rc_id,
                                                        dayofweek,
                                                        sum(hour_work) as total_hour_per_day
                                                        from (
                                                            select
                                                                rc_id,
                                                                nameday,
                                                                count(dayofweek)"day",
                                                                dayofweek,
                                                                hour_work
                                                            from (
                                                                select *,
                                                                    rc.id rc_id,
                                                                    rca.name as nameday,
                                                                    (hour_to - hour_from) hour_work from resource_calendar rc
                                                                    left join resource_calendar_attendance rca on rc.id = rca.calendar_id
                                                                    group by dayofweek,rc.id,rca.id order by dayofweek
                                                                )a group by
                                                                    hour_to,
                                                                    hour_from,
                                                                    nameday,
                                                                    rc_id,
                                                                    dayofweek,
                                                                    hour_work order by nameday asc
                                                            )b group by rc_id,dayofweek
                                            )a on hrc.working_hours = a.rc_id group by employee_id , wage,total_hour_per_day,contract_type, contract_period,date_end
                                          )b on b.employee_id = etat.employee_id group by create_date,vehicle_id,date_end,
                                        asset,
                                        mo_id,
                                        mastertask_id,
                                        etat.employee_id,activity_id,start_time,end_time,
                                        wage,total_hour_per_day,total_hour_per_week,
                                        contract_type,
                                        contract_period,date_activity_transport
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
    product_id = fields.Many2one('product.product')

    def init(self, cr):
        cr.execute("""create or replace view view_cost_workshop_sparepart as
                 select row_number() over()id,mo_id, sum(total_cost) as total_amount,product_id,fleet_id as vehicle_id,month_log,year_log,parent_id from(
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
                    select owner_id,c.product_id,qty_product,cost from estate_workshop_actual_sparepart ewas
                inner join (
                    select pp.id as product_id,pt.id product_tmpl_id,cost from product_product pp
                    inner join product_template pt on pp.product_tmpl_id = pt.id
                    inner join product_price_history pph on pp.id=pph.product_id
                )c on ewas.product_id = c.product_id
                )ewas on mo.id = ewas.owner_id)b
                group by month_log,year_log,asset_id,mo_id,product_id,qty_product,cost,fleet_id,month_log,year_log)a
                group by mo_id,fleet_id,month_log,year_log,product_id,parent_id""")

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

class InheritVsummaryCostVehicle(models.Model):

    _inherit = 'v.summary.cost.vehicle'

    service_internal_ids = fields.One2many('view.service.internal.detail','parent_id')

class ViewServiceInternalDetail(models.Model):

    _name="view.service.internal.detail"
    _description = "Detail for cost Service Internal every month vehicle"
    _auto = False
    _order='aa_id'

    id = fields.Integer()
    aa_id = fields.Many2one('asset.asset')
    maintenance_type_id = fields.Integer()
    requester_id = fields.Many2one('hr.employee')
    license_plate= fields.Char()
    cause = fields.Char('Cause')
    accident_location = fields.Many2one('stock.location')
    total_amount = fields.Float('Amount')
    parent_id = fields.Many2one('v.summary.cost.vehicle')

    def init(self, cr):
        cr.execute("""create or replace view view_service_internal_detail as
                    select row_number() over()id,
                           (month_log::text||year_log::text||fv_id::text)::Integer parent_id,
                           aa_id,
                           requester_id,license_plate,
                           cause,maintenance_type_id,
                           accident_location,total_amount from(
                           select
                                mo.date_execution as date_execution,
                                date_part('day',mo.date_execution) day_log,
                                date_part('month',mo.date_execution) month_log,
                                date_part('year',mo.date_execution) year_log,
                                aa_id,fv_id,
                                requester_id,license_plate,
                                cause,type_service_handling as maintenance_type_id,
                                sum(vscwd.total_amount) as total_amount,
                                mo.location_id as accident_location from (
                                    select	aa.id as aa_id, aa.fleet_id as fv_id,*  from asset_asset aa
                                        inner join fleet_vehicle fv on aa.fleet_id = fv.id
                                        )fleet
                                        left join mro_order mo on fleet.aa_id = mo.asset_id
                                        left join v_summary_cost_workshop_detail vscwd on fleet.fv_id = vscwd.vehicle_id
                                where fleet.type_asset = '1' and mo.state = 'done'
                                group by date_execution,aa_id,fv_id,requester_id,license_plate,
                                        cause,maintenance_type_id,accident_location
                                )mro
                        group by aa_id,month_log,year_log,fv_id,requester_id,license_plate,
                                cause,maintenance_type_id,
                                accident_location,total_amount""")

class ViewSummaryCostVehicleDetail(models.Model):

    _name="v.summary.cost.vehicle.detail"
    _description = "Detail for cost every month vehicle"
    _auto = False
    _order='vehicle_id'

    id = fields.Integer('id')
    type_log = fields.Text('Type Log')
    vehicle_id = fields.Many2one('fleet.vehicle')
    count = fields.Integer('')
    month_log_text = fields.Text('Month')
    year_log_text = fields.Text('Year')
    amount = fields.Float('Amount')
    parent_id = fields.Many2one('v.summary.cost.vehicle')

    def init(self, cr):
        cr.execute("""create or replace view v_summary_cost_vehicle_detail as
                select detail.*, (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id from (
                    select row_number() over()id, type_log, vehicle_id, "count", to_char(to_timestamp (month_log::text, 'MM'), 'Month') as month_log_text, year_log::text as year_log_text, amount, month_log, year_log  from (
                            select
                                'Fuel' as type_log, vehicle_id,count(*) "count",month_log, year_log, sum(cost_amount) amount
                            from (
                                    select fvlf.*,fvc.vehicle_id, date_part('month', fvlf.create_date) month_log, date_part('year', fvlf.create_date) year_log from fleet_vehicle_cost fvc inner join fleet_vehicle_log_fuel fvlf on fvc.id = fvlf.cost_id
                                ) a group by vehicle_id, month_log, year_log
                            union
                            select
                                'External Service' as type_log, vehicle_id,count(*) "count",month_log, year_log, sum(cost_amount) amount
                            from (
                                    select fvlf.*,fvc.vehicle_id, date_part('month', fvlf.create_date) month_log, date_part('year', fvlf.create_date) year_log from fleet_vehicle_cost fvc inner join fleet_vehicle_log_services fvlf on fvc.id = fvlf.cost_id
                                ) a group by vehicle_id, month_log, year_log
                            union
                            select
                                'Oil' as type_log, vehicle_id,count(*) "count",month_log, year_log, sum(cost_amount) amount
                            from (
                                    select fvlf.*,fvc.vehicle_id, date_part('month', fvlf.create_date) month_log, date_part('year', fvlf.create_date) year_log from fleet_vehicle_cost fvc inner join estate_vehicle_log_oil fvlf on fvc.id = fvlf.cost_id
                                ) a group by vehicle_id, month_log, year_log
                            union
                            select 'Workshop Mecanic' as type_log,vehicle_id,count(*) "count",month_log,year_log,sum(total_amount) amount from(
                            	select * from view_timesheet_mecanic_totalamounts
                            )workmec group by vehicle_id, month_log, year_log
                            union
                            select 'Workshop Sparepart' as type_log,vehicle_id,count(*) "count",month_log,year_log,sum(total_amount) amount from(
                            		select * from view_cost_workshop_sparepart)workpart group by vehicle_id, month_log, year_log
                            union
                            select
                                'Other Service' as type_log, vehicle_id,count(*) "count",month_log, year_log, sum(amount) amount
                            from (
                                    select fvlf.*,fvc.vehicle_id, date_part('month', fvlf.create_date) month_log, date_part('year', fvlf.create_date) year_log,(fvlf.price_per_service * fvlf.unit) amount from fleet_vehicle_cost fvc inner join estate_vehicle_log_otherservice fvlf on fvc.id = fvlf.cost_id
                                ) a group by vehicle_id, month_log, year_log
                            union
                            select 'Basis Premi' as type_log,c.vehicle_id,count(*) "count",c.month_log ,c.year_log,
                            CASE WHEN d.wage is null THEN 0
                                ELSE ((c.total_trip/c.total_trip_vehicle)* d.wage)
                               END amount
                                from (
                            select
                                'Timesheet' as timesheet, a.employee_id, a.month_log, a.year_log, a.vehicle_id , a.total_trip,
                                b.total_trip_vehicle
                                from (
                                    select ts.vehicle_id, count(ts.id) total_trip,ts.employee_id,
                                    date_part('month', ts.date_activity_transport) month_log,
                                    date_part('year', ts.date_activity_transport) year_log
                                        from estate_timesheet_activity_transport ts
                                        inner join fleet_vehicle fv on ts.vehicle_id = fv.id
                                    group by vehicle_id, month_log,year_log ,employee_id
                            )a inner join
                            (
                                select count(ts.id) total_trip_vehicle,
                                    ts.employee_id,
                                    ts.vehicle_id,
                                    date_part('month', ts.date_activity_transport) month_log,
                                    date_part('year', ts.date_activity_transport) year_log
                                        from estate_timesheet_activity_transport ts
                                    group by month_log,year_log ,employee_id,ts.vehicle_id
                            )b on a.vehicle_id = b.vehicle_id and a.employee_id = b.employee_id and a.month_log = b.month_log and a.year_log = b.year_log
                        ) c left join (select * from (
                                select hre.id as hre_id ,hrj.name as hrj_name, * from hr_employee hre
                                    inner join hr_job hrj on hre.job_id = hrj.id)a
                                    right join hr_contract hrc on hrc.employee_id = a.hre_id
                                    where hrc.date_end is null and hrj_name = 'Driver' or hrj_name = 'Helper')d on d.hre_id = c.employee_id
                                    where d.date_end is null and hrj_name = 'Driver' or hrj_name = 'Helper'
                            group by c.vehicle_id, c.month_log , c.year_log , d.wage , c.total_trip, c.total_trip_vehicle order by month_log
                            ) a order by type_log, month_log, year_log asc
                )detail""")

class ViewTimesheetMechanicWorkshop(models.Model):

    _name = 'v.timesheet.mechanic.workshop'
    _description = " view timesheet mechanic for vehicle"
    _auto = False
    _order='year_log'

    id = fields.Integer()
    asset_id = fields.Many2one('asset.asset')
    task_id = fields.Many2one('mro.task')
    mastertask_id = fields.Many2one('estate.workshop.mastertask')
    employee_id = fields.Many2one('hr.employee')
    vehicle_id = fields.Many2one('fleet.vehicle')
    start_time = fields.Float()
    end_time = fields.Float()
    dc_type = fields.Integer()

    def init(self, cr):
        cr.execute("""create or replace view v_timesheet_mechanic_workshop as
                select
                    emt.id as id,
                    ts.create_date as ts_create_date,
                    asset_id,
                    task_id,
                    mastertask_id,
                    vehicle_id,
                    employee_id,
                    owner_id,
                    start_time,end_time,
                    dc_type from estate_mecanic_timesheet emt
                    inner join estate_timesheet_activity_transport ts on emt.timesheet_id=ts.id""")

class ViewCostWorkshop(models.Model):

    _name = 'v.cost.workshop'
    _description = " view cost workshop vehicle"
    _auto = False
    _order='year_log'

    id = fields.Integer()
    parent_id = fields.Many2one('v.workshop.working.account.vehicle')
    mo_id = fields.Many2one('mro.order')
    total_amount = fields.Float('Total Amount')
    month_log = fields.Integer('Month')
    year_log = fields.Integer('Year')
    month_log_text = fields.Text('Month')
    year_log_text = fields.Text('Year')
    vehicle_id = fields.Many2one('fleet.vehicle')
    type_log = fields.Text('Type Log')
    count = fields.Integer('')

    def init(self, cr):
        cr.execute("""create or replace view v_cost_workshop as
                select detail.*, (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id from(
                     select row_number() over()id,type_log,mo_id,"count",total_amount,month_log,year_log,
                     to_char(to_timestamp (month_log::text, 'MM'), 'Month') as month_log_text,year_log::text as year_log_text,vehicle_id from(
                            select 'Cost Labour' as type_log,mo_id,count(*)"count",sum(total_amount) as total_amount,year_log,month_log,vehicle_id from(
                            select * from view_timesheet_mecanic_totalamounts
                                    )cl group by mo_id,year_log,month_log,vehicle_id
                            union
                            select 'Cost Part'as type_log,mo_id,count(*)"count",sum(total_amount) as total_amount,year_log,month_log,vehicle_id from(
                                select * from view_cost_workshop_sparepart
                                )cs group by mo_id,year_log,month_log,vehicle_id
                          )utot order by mo_id asc
                    )detail""")

class ViewTimesheetMechanicDetail(models.Model):

    _name = 'v.timesheet.mechanic.workshop.detail'
    _description = "Timesheet Mechanic for vehicle"
    _auto = False
    _order='year_log'

    id = fields.Integer()
    parent_id = fields.Many2one('v.workshop.working.account.vehicle')
    ts_create_date = fields.Date()
    day_log = fields.Text()
    month_log = fields.Text()
    year_log = fields.Text()
    start_time = fields.Float()
    end_time = fields.Float()
    asset_id = fields.Many2one('asset.asset')
    vehicle_id = fields.Many2one('fleet.vehicle')
    time_per_activity = fields.Float()
    task_id = fields.Many2one('mro.task')
    mastertask_id = fields.Many2one('estate.workshop.mastertask')
    employee_id = fields.Many2one('hr.employee')


    def init(self, cr):
        cr.execute("""create or replace view v_timesheet_mechanic_workshop_detail as
                select row_number() over()id,
                (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id,
                start_time,end_time,ts_create_date,
                (end_time - start_time) as time_per_activity,
                day_log,month_log,year_log,
                asset_id,vehicle_id,task_id,mastertask_id,employee_id from (
                    select date_part('month', ts_create_date) month_log,
                        date_part('day', ts_create_date) day_log,
                        date_part('year', ts_create_date) year_log,* from v_timesheet_mechanic_workshop
                    )tsm""")

class ViewWorkshopSummarySparepart(models.Model):

    _name = 'v.workshop.summary.sparepart'
    _description = "Summary Sparepart for vehicle"
    _auto = False
    _order='year_log'

    id = fields.Integer()
    mro_id = fields.Many2one('mro.order')
    parent_id = fields.Many2one('v.workshop.working.account.vehicle')
    product_id = fields.Many2one('product.product')
    count = fields.Integer()
    qty_product = fields.Float()
    date_execution = fields.Date()
    cost = fields.Float()
    amount = fields.Float()
    fleet_id = fields.Many2one('fleet.vehicle')
    year_log = fields.Text()

    def init(self, cr):
        cr.execute("""create or replace view v_workshop_summary_sparepart as
            select row_number() over()id,
                (month_log::text||year_log::text||fleet_id::text)::Integer parent_id,mro_id,
                product_id,qty_product,date_execution,cost,amount,"count",fleet_id,year_log
                from (
                     select
                     	mro_id,
                        fleet_id,
                        mro.product_id as product_id,
                        asset_id,count(*)"count",
                        date_execution,
                        date_part('month', date_execution) month_log,
                        date_part('year', date_execution) year_log,
                        qty_product,cost,
                        (cost * qty_product) as amount
                        from asset_asset aa
                        right join (
                            select
                            	mo.id as mro_id,
                                product_id,
                                asset_id,
                                date_execution,
                                qty_product from mro_order mo
                            inner join
                                estate_workshop_actual_sparepart ewas
                                on mo.id = ewas.owner_id
                        )mro on mro.asset_id=aa.id
                        inner join (
                         select pp.id as pp_id,cost
                            from
                                product_product pp
                            inner join
                                product_price_history pph on pph.product_id = pp.id
                        )ppph on mro.product_id= ppph.pp_id group by mro.product_id,fleet_id,asset_id,mro_id,
                        date_execution,
                        month_log,
                        year_log,
                        qty_product,cost
                    )partworkshop order by mro_id asc""")

class ViewBasicSalaryMechanic(models.Model):

    _name = 'view.basic.salary.mechanic'
    _description = "Basic Salary Mechanic"
    _auto = False
    _order='year_log_text'

    id = fields.Integer()
    date_activity_transport = fields.Date()
    day_log_text = fields.Text()
    month_log_text = fields.Text()
    year_log_text = fields.Text()
    vehicle_id = fields.Many2one('fleet.vehicle')
    total_trip = fields.Integer()
    total_trip_vehicle = fields.Integer()
    count = fields.Integer()
    employee_id = fields.Many2one('hr.employee')
    wage = fields.Float()
    amount = fields.Float()
    parent_id = fields.Many2one('v.workshop.working.account.vehicle')

    def init(self, cr):
        cr.execute("""create or replace view view_basic_salary_mechanic as
            select row_number() over()id,date_activity_transport,total_trip,vehicle_id,count(*) "count",
            to_char(to_timestamp (day_log::text, 'MM'), 'Day') as day_log_text,
            to_char(to_timestamp (month_log::text, 'MM'), 'Month') as month_log_text,
            (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id,
            wage,total_trip_vehicle,c.employee_id,
            year_log::text as year_log_text,
                CASE WHEN d.wage is null THEN 0
                    ELSE ((c.total_trip/c.total_trip_vehicle)* d.wage)
                   END amount
                    from (
                select
                    'Timesheet' as timesheet,date_activity_transport, a.employee_id,a.day_log,a.month_log, a.year_log, a.vehicle_id , a.total_trip,
                    b.total_trip_vehicle
                    from (
                        select date_activity_transport,ts.vehicle_id, count(ts.id) total_trip,ts.employee_id,
                        date_part('day',ts.date_activity_transport) day_log,
                        date_part('month', ts.date_activity_transport) month_log,
                        date_part('year', ts.date_activity_transport) year_log
                            from estate_timesheet_activity_transport ts
                            inner join fleet_vehicle fv on ts.vehicle_id = fv.id
                        group by vehicle_id,day_log, month_log,year_log ,employee_id,date_activity_transport
                )a inner join
            (
                select count(ts.id) total_trip_vehicle,
                    ts.employee_id,
                    ts.vehicle_id,
                    date_part('month', ts.date_activity_transport) month_log,
                    date_part('year', ts.date_activity_transport) year_log
                        from estate_timesheet_activity_transport ts
                    group by month_log,year_log ,employee_id,ts.vehicle_id
            )b on a.vehicle_id = b.vehicle_id and a.employee_id = b.employee_id and a.month_log = b.month_log and a.year_log = b.year_log
        ) c left join (select * from (
                select hre.id as hre_id ,hrj.name as hrj_name, * from hr_employee hre
                    inner join hr_job hrj on hre.job_id = hrj.id)a
                    right join hr_contract hrc on hrc.employee_id = a.hre_id
                    where hrc.date_end is null and hrj_name = 'Mechanic')d
                    on d.hre_id = c.employee_id
                    where d.date_end is null and hrj_name = 'Mechanic'
            group by c.vehicle_id,
            c.month_log , c.year_log ,
            d.wage , c.total_trip,
            c.total_trip_vehicle,c.employee_id,date_activity_transport,day_log_text,month_log_text order by month_log""")

class ViewWorkshopWorkingAccountVehicle(models.Model):

    _name = 'v.workshop.working.account.vehicle'
    _description = "workshop working account for vehicle"
    _auto = False
    _order='year_log'

    id = fields.Integer()
    vehicle_id = fields.Many2one('fleet.vehicle')
    cost_ids = fields.One2many('v.cost.workshop','parent_id')
    timesheet_mechanic_ids = fields.One2many('v.timesheet.mechanic.workshop.detail','parent_id')
    sparepart_ids = fields.One2many('v.workshop.summary.sparepart','parent_id')
    basicsalary_ids = fields.One2many('view.basic.salary.mechanic','parent_id')
    month_log = fields.Text('Month')
    year_log = fields.Text('Year')
    month_log_text = fields.Text('Month')
    year_log_text = fields.Text('Year')
    ts_create_date = fields.Date('Date')
    total_time = fields.Float('Total Time')
    total_amount_per_month = fields.Float('Amount')
    amount_per_hour = fields.Float('Amount Per Hour')

    def init(self, cr):
        cr.execute("""create or replace view v_workshop_working_account_vehicle as
        select e.parent_id as id,
                e.year_log,
                e.month_log,
                e.vehicle_id,
                month_log_text,
                ts_create_date,
                year_log_text,
                Total_time as total_time,
                Total_amount_per_Month as total_amount_per_month,
                case when Total_time is null then  Total_amount_per_Month
                    else (total_amount_per_month / total_time) end amount_per_hour
                from (
                        select
                            (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id,
                            to_char(to_timestamp (month_log::text, 'MM'), 'Month') as month_log_text,
                            year_log::text as year_log_text,to_date(to_char(ts_create_date,'MM-DD-YYYY'),'MM-DD-YYYY') ts_create_date,
                            vehicle_id,
                            sum(time_per_activity) as Total_time from (
                                select ts_create_date,
                                asset_id,vehicle_id,
                                date_part('month', ts.ts_create_date) month_log,
                                date_part('year', ts.ts_create_date) year_log,
                                ts.end_time,
                                ts.start_time,
                                (ts.end_time - ts.start_time) as time_per_activity
                                from v_timesheet_mechanic_workshop ts)a group by vehicle_id ,month_log, year_log,ts_create_date
                    )d right join (
                            select
                                parent_id,
                                vehicle_id,
                                year_log,
                                month_log,
                                sum(total_amount) as Total_amount_per_Month from (
                                select
                                    parent_id,
                                    type_log,
                                    month_log,
                                    year_log,
                                    vehicle_id,
                                    total_amount
                                from v_summary_cost_workshop_detail)b
                                group by parent_id,vehicle_id , year_log,month_log
                          )e on d.parent_id = e.parent_id""")



