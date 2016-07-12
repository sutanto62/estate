from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal

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
                            select
                                'Other Service' as type_log, vehicle_id,count(*) "count",month_log, year_log, sum(amount) amount
                            from (
                                    select fvlf.*,fvc.vehicle_id, date_part('month', fvlf.create_date) month_log, date_part('year', fvlf.create_date) year_log,(fvlf.price_per_service * fvlf.unit) amount from fleet_vehicle_cost fvc inner join estate_vehicle_log_otherservice fvlf on fvc.id = fvlf.cost_id
                                ) a group by vehicle_id, month_log, year_log
                            union
                            select 'Basis Premi' as type_log,c.vehicle_id,count(*) "count",c.month_log ,c.year_log,
                            CASE WHEN hrc.wage is null THEN 0
                                ELSE ((c.total_trip/c.total_trip_vehicle)* hrc.wage)
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
                                    group by  month_log,year_log ,employee_id,ts.vehicle_id
                            )b on a.vehicle_id = b.vehicle_id and a.employee_id = b.employee_id and a.month_log = b.month_log and a.year_log = b.year_log
                        ) c left join hr_contract hrc on c.employee_id = hrc.employee_id where hrc.date_end is null group by c.vehicle_id, c.month_log , c.year_log , hrc.wage , c.total_trip, c.total_trip_vehicle order by month_log
                        ) a order by type_log, month_log, year_log asc
        )detail""")

class ViewSummaryCostVehicle(models.Model):

    _name = 'v.summary.cost.vehicle'
    _description = " summary cost for vehicle"
    _auto = False
    _order='year_log_text'

    id = fields.Integer()
    vehicle_id = fields.Many2one('fleet.vehicle')
    summary_ids = fields.One2many('v.summary.cost.vehicle.detail','parent_id')
    fuelsummary_ids = fields.One2many('view.fuel.vehicle.detail','parent_id')
    oilsummary_ids = fields.One2many('view.oil.vehicle.detail','parent_id')
    servicesummary_ids = fields.One2many('view.service.vehicle.detail','parent_id')
    sparepartsummary_ids = fields.One2many('view.sparepart.vehicle.detail','parent_id')
    otherservicesummary_ids = fields.One2many('view.otherservice.vehicle.detail','parent_id')
    # workshopamount_ids = fields.One2many('v.summary.cost.workshop.detail','parent_id')
    basispremi_ids = fields.One2many('view.basispremi.vehicle.detail','parent_id')
    timesheetsummary_ids = fields.One2many('view.summary.timesheet.vehicle','parent_id')
    month_log_text = fields.Text('Month')
    year_log_text = fields.Text('Year')
    total_time = fields.Float('Total Time')
    total_amount_per_month = fields.Float('Amount')
    amount_per_hour = fields.Float('Amount Per Hour')
    # parent_id = fields.Text()

    def init(self, cr):
        cr.execute("""create or replace view v_summary_cost_vehicle as
        select e.parent_id as id,
            e.year_log_text,
            e.month_log_text,
            e.vehicle_id,
            Total_time as total_time,
            Total_amount_per_Month as total_amount_per_month,
            case when Total_time is null then  Total_amount_per_Month
            	else (total_amount_per_month / total_time) end amount_per_hour
            from (
                    select
                        (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id,
                        to_char(to_timestamp (month_log::text, 'MM'), 'Month') as month_log_text,
                        year_log::text as year_log_text,
                        vehicle_id,
                        sum(time_per_activity) as Total_time from (
                            select create_date,
                            vehicle_id,
                            date_part('month', ts.create_date) month_log,
                            date_part('year', ts.create_date) year_log,
                            ts.end_time,
                            ts.start_time,
                            (ts.end_time - ts.start_time) as time_per_activity
                            from estate_timesheet_activity_transport ts)a group by vehicle_id ,month_log, year_log
                )d right join (
                        select
                            parent_id,
                            vehicle_id,
                            year_log_text,
                            month_log_text,
                            sum(amount) as Total_amount_per_Month from (
                            select
                                parent_id,
                                type_log,
                                month_log_text,
                                year_log_text,
                                vehicle_id,
                                amount
                            from v_summary_cost_vehicle_detail)b
                            group by parent_id,vehicle_id , year_log_text,month_log_text )e on d.parent_id = e.parent_id""")

class ViewFuelSummaryVehicle(models.Model):

    _name = 'view.fuel.vehicle.detail'
    _description = " Summary Fuel cost for vehicle"
    _auto = False
    _order='year_log_text'

    id = fields.Integer()
    create_date = fields.Date()
    day_log_text = fields.Text()
    month_log_text = fields.Text()
    year_log_text = fields.Text()
    vehicle_id = fields.Many2one('fleet.vehicle')
    liter= fields.Float()
    price_per_liter = fields.Float()
    cost_amount = fields.Float()
    parent_id = fields.Many2one('v.summary.cost.vehicle')
    inv_ref = fields.Char()
    vendor_id = fields.Many2one('res.partner')

    def init(self, cr):
        cr.execute("""create or replace view view_fuel_vehicle_detail as
                select row_number() over()id,
                    a.create_date,
                    to_char(to_timestamp (day_log::text, 'MM'), 'Day') as day_log_text,
                    to_char(to_timestamp (month_log::text, 'MM'), 'Month') as month_log_text,
                    year_log::text as year_log_text,
                    a.vehicle_id,
                    a.liter,a.price_per_liter,a.cost_amount,
                    (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id,a.inv_ref,a.vendor_id
                from (
                    select fvlf.*,fvc.vehicle_id,
                        date_part('day',
                       fvlf.create_date) day_log,
                       date_part('month',
                       fvlf.create_date) month_log,
                       date_part('year',
                       fvlf.create_date) year_log
                    from fleet_vehicle_cost fvc
                    inner join
                    fleet_vehicle_log_fuel fvlf
                    on fvc.id = fvlf.cost_id
                )a;""")

class ViewOilSummaryVehicle(models.Model):

    _name = 'view.oil.vehicle.detail'
    _description = " Summary Oil cost for vehicle"
    _auto = False
    _order='year_log_text'

    id = fields.Integer()
    create_date = fields.Date()
    day_log_text = fields.Text()
    month_log_text = fields.Text()
    year_log_text = fields.Text()
    vehicle_id = fields.Many2one('fleet.vehicle')
    product_id = fields.Many2one('product.product')
    liter= fields.Float()
    price_per_liter = fields.Float()
    cost_amount = fields.Float()
    parent_id = fields.Many2one('v.summary.cost.vehicle')
    inv_ref = fields.Char()
    vendor_id = fields.Many2one('res.partner')

    def init(self, cr):
        cr.execute("""create or replace view view_oil_vehicle_detail as
                select row_number() over()id,
                        a.create_date,
                        to_char(to_timestamp (day_log::text, 'MM'), 'Day') as day_log_text,
                        to_char(to_timestamp (month_log::text, 'MM'), 'Month') as month_log_text,
                        year_log::text as year_log_text,
                        a.vehicle_id,a.product_id,
                        a.liter,a.price_per_liter,a.cost_amount,
                        (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id,
                        a.inv_ref,a.vendor_id
                            from (
                                    select fvlf.*,fvc.vehicle_id,
                                    date_part('day',fvlf.create_date) day_log,
                                    date_part('month', fvlf.create_date) month_log,
                                    date_part('year', fvlf.create_date) year_log
                                    from fleet_vehicle_cost fvc inner join estate_vehicle_log_oil fvlf on fvc.id = fvlf.cost_id
                                )a;""")

class ViewServiceSummaryVehicle(models.Model):

    _name = 'view.service.vehicle.detail'
    _description = " Summary Service cost for vehicle"
    _auto = False
    _order='year_log_text'

    id = fields.Integer()
    create_date = fields.Date()
    day_log_text = fields.Text()
    month_log_text = fields.Text()
    year_log_text = fields.Text()
    vehicle_id = fields.Many2one('fleet.vehicle')
    notes = fields.Text()
    purchaser_id = fields.Many2one('res.partner')
    cost_amount = fields.Float()
    parent_id = fields.Many2one('v.summary.cost.vehicle')
    inv_ref = fields.Char()
    vendor_id = fields.Many2one('res.partner')

    def init(self, cr):
        cr.execute("""create or replace view view_service_vehicle_detail as
                select row_number() over()id,
                        a.create_date,
                        to_char(to_timestamp (day_log::text, 'MM'), 'Day') as day_log_text,
                        to_char(to_timestamp (month_log::text, 'MM'), 'Month') as month_log_text,
                        year_log::text as year_log_text,
                        a.vehicle_id,a.notes,a.purchaser_id,
                        a.cost_amount,
                        (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id,
                        a.inv_ref,a.vendor_id
                            from (
                                    select fvlf.*,fvc.vehicle_id,date_part('day',fvlf.create_date) day_log,
                                    date_part('month', fvlf.create_date) month_log,
                                    date_part('year', fvlf.create_date) year_log
                                    from fleet_vehicle_cost fvc
                                    inner join fleet_vehicle_log_services fvlf on fvc.id = fvlf.cost_id
                                    ) a;""")

class ViewSparepartSummaryVehicle(models.Model):

    _name = 'view.sparepart.vehicle.detail'
    _description = " Summary Sparepart cost for vehicle"
    _auto = False
    _order='year_log_text'

    id = fields.Integer()
    create_date = fields.Date()
    day_log_text = fields.Text()
    month_log_text = fields.Text()
    year_log_text = fields.Text()
    vehicle_id = fields.Many2one('fleet.vehicle')
    product_id = fields.Many2one('product.product')
    purchaser_id = fields.Many2one('res.partner')
    unit= fields.Float()
    price_per_unit = fields.Float()
    amount = fields.Float()
    parent_id = fields.Many2one('v.summary.cost.vehicle')
    inv_ref = fields.Char()
    notes = fields.Text()
    vendor_id = fields.Many2one('res.partner')

    def init(self, cr):
        cr.execute("""create or replace view view_sparepart_vehicle_detail as
                    select row_number() over()id,
                        a.create_date,
                        to_char(to_timestamp (day_log::text, 'MM'), 'Day') as day_log_text,
                        to_char(to_timestamp (month_log::text, 'MM'), 'Month') as month_log_text,
                        year_log::text as year_log_text,
                        a.vehicle_id,a.purchaser_id,a.product_id,
                        a.unit,a.price_per_unit,
                        sum(amount) amount,a.notes,
                        (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id,
                        a.inv_ref,a.vendor_id
                            from (
                                    select fvlf.*,fvc.vehicle_id,
                                    date_part('day',fvlf.create_date) day_log,
                                    date_part('month', fvlf.create_date) month_log,
                                    date_part('year', fvlf.create_date) year_log,
                                    (fvlf.price_per_unit * fvlf.unit) amount
                                    from fleet_vehicle_cost fvc
                                    inner join estate_vehicle_log_sparepart fvlf on fvc.id = fvlf.cost_id
                                    )a group by create_date , day_log , month_log , year_log , vehicle_id, notes, purchaser_id , product_id , unit , price_per_unit , inv_ref ,vendor_id;""")

class ViewOtherServiceSummaryVehicle(models.Model):

    _name='view.otherservice.vehicle.detail'
    _description = " Summary Other Service cost for vehicle"
    _auto = False
    _order='year_log_text'

    id = fields.Integer()
    create_date = fields.Date()
    day_log_text = fields.Text()
    month_log_text = fields.Text()
    year_log_text = fields.Text()
    vehicle_id = fields.Many2one('fleet.vehicle')
    product_id = fields.Many2one('product.product')
    purchaser_id = fields.Many2one('res.partner')
    unit= fields.Float()
    price_per_service = fields.Float()
    amount = fields.Float()
    parent_id = fields.Many2one('v.summary.cost.vehicle')
    inv_ref = fields.Char()
    notes = fields.Text()
    vendor_id = fields.Many2one('res.partner')

    def init(self, cr):
        cr.execute("""create or replace view view_otherservice_vehicle_detail as
               select row_number() over()id,
                    a.create_date,
                    to_char(to_timestamp (day_log::text, 'MM'), 'Day') as day_log_text,
                    to_char(to_timestamp (month_log::text, 'MM'), 'Month') as month_log_text,
                    year_log::text as year_log_text,
                    a.vehicle_id,a.purchaser_id,a.product_id,
                    a.unit,a.price_per_service,
                    sum(amount) amount,a.notes,
                    (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id,
                    a.inv_ref,a.vendor_id
                        from (
                            select fvlf.*,fvc.vehicle_id,
                            date_part('day',fvlf.create_date) day_log,
                            date_part('month', fvlf.create_date) month_log,
                            date_part('year', fvlf.create_date) year_log,
                            (fvlf.price_per_service * fvlf.unit) amount
                            from fleet_vehicle_cost fvc
                            inner join estate_vehicle_log_otherservice fvlf on fvc.id = fvlf.cost_id
                            ) a group by create_date ,
                            day_log ,
                            month_log ,
                            year_log ,
                            vehicle_id,
                            notes, purchaser_id ,
                            product_id , unit , price_per_service , inv_ref ,vendor_id;""")


class ViewBasisPremiSummaryVehicle(models.Model):

    _name = 'view.basispremi.vehicle.detail'
    _description = " Summary Basis Premi and Premi cost for vehicle"
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
    parent_id = fields.Many2one('v.summary.cost.vehicle')

    def init(self, cr):
        cr.execute("""create or replace view view_basispremi_vehicle_detail as
            select row_number() over()id,c.date_activity_transport,c.total_trip,c.vehicle_id,count(*) "count",
            to_char(to_timestamp (day_log::text, 'MM'), 'Day') as day_log_text,
            to_char(to_timestamp (month_log::text, 'MM'), 'Month') as month_log_text,
            (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id,
            wage,total_trip_vehicle,c.employee_id,
            year_log::text as year_log_text,
                CASE WHEN hrc.wage is null THEN 0
                    ELSE ((c.total_trip/c.total_trip_vehicle)* hrc.wage)
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
                    date_part('day',ts.date_activity_transport) day_log,
                    date_part('month', ts.date_activity_transport) month_log,
                    date_part('year', ts.date_activity_transport) year_log
                        from estate_timesheet_activity_transport ts
                    group by  day_log,month_log,year_log ,employee_id
            )b on a.employee_id = b.employee_id and a.month_log = b.month_log and a.year_log = b.year_log
        ) c left join hr_contract hrc on c.employee_id = hrc.employee_id where hrc.date_end is null
        group by c.vehicle_id,c.day_log,c.employee_id,
        c.month_log ,
        c.year_log ,
        hrc.wage ,
        c.total_trip,
        c.total_trip_vehicle ,c.date_activity_transport
        order by month_log;""")

class ViewTimesheetSummaryVehicle(models.Model):

    _name ='view.summary.timesheet.vehicle'
    _description = " Summary Timesheet cost per hour for vehicle"
    _auto = False
    _order='year_log_text'

    id = fields.Integer()
    parent_id = fields.Many2one('v.summary.cost.vehicle')
    create_date = fields.Date()
    day_log_text = fields.Text()
    month_log_text = fields.Text()
    year_log_text = fields.Text()
    start_location = fields.Many2one('estate.block.template')
    end_location = fields.Many2one('estate.block.template')
    factor_id = fields.Many2one('master.factor.multiple')
    distance_location = fields.Float()
    activity_id = fields.Many2one('estate.activity')
    total_hour = fields.Float(digits=(2,2))
    amount_per_hour = fields.Float()
    total_amount_per_hour = fields.Float()

    def init(self, cr):
        cr.execute("""create or replace view view_summary_timesheet_vehicle as
            select row_number() over()id,
                f.parent_id ,
                create_date,
                day_log_text,
                f.month_log_text,
                f.year_log_text,
                start_location,
                end_location,
                factor_id,
                distance_location,
                activity_id,
                total_hour,
                amount_per_hour,
                (total_hour * amount_per_hour) as total_amount_per_hour
                from (
                select
                    parent_id,
                    create_date,
                    day_log_text,
                    month_log_text,
                    year_log_text,
                    vehicle_id,
                    d.start_location,
                    d.end_location,
                    distance_location,
                    factor_id,
                    activity_id,
                    total_hour
                from (
                select
                    (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id,
                    vehicle_id,
                    create_date,
                    to_char(to_timestamp (day_log::text, 'MM'), 'Day') as day_log_text,
                    to_char(to_timestamp (month_log::text, 'MM'), 'Month') as month_log_text,
                    year_log::text as year_log_text,
                    start_location,end_location,activity_id,(a.end_time - a.start_time) as total_hour
                    from (
                select
                    create_date,
                    vehicle_id,
                    date_part('day', ts.create_date) day_log,
                    date_part('month', ts.create_date) month_log,
                    date_part('year', ts.create_date) year_log,
                    start_location,
                    end_location,
                    activity_id,
                    ts.end_time,
                    ts.start_time,
                    (ts.end_time - ts.start_time) as time_per_activity
                from
                    estate_timesheet_activity_transport ts)a
                    )d inner join (
                select
                    start_location,
                    end_location,
                    distance_location,
                    path_price,
                    factor_id
                from path_location pl)e on d.start_location = e.start_location and d.end_location = e.end_location)f inner join (
                select
                e.parent_id,
                e.year_log_text,
                e.month_log_text,
                e.vehicle_id,total_time,
                total_amount_per_Month,
                (total_amount_per_month / total_time) as amount_per_hour from (
                select
                    (month_log::text||year_log::text||vehicle_id::text)::Integer parent_id,
                    to_char(to_timestamp (month_log::text, 'MM'), 'Month') as month_log_text,
                    year_log::text as year_log_text,
                    vehicle_id,
                    sum(time_per_activity) as total_time from (
                        select create_date,
                        vehicle_id,
                        date_part('month', ts.create_date) month_log,
                        date_part('year', ts.create_date) year_log,
                        ts.end_time,
                        ts.start_time,
                        (ts.end_time - ts.start_time) as time_per_activity
                        from estate_timesheet_activity_transport ts)a group by vehicle_id ,month_log, year_log
            )d right join (
                    select
                        parent_id,
                        vehicle_id,
                        year_log_text,
                        month_log_text,
                        sum(amount) as total_amount_per_Month from (
                        select
                            parent_id,
                            type_log,
                            month_log_text,
                            year_log_text,
                            vehicle_id,
                            amount
                        from v_summary_cost_vehicle_detail)b
                        group by
                            parent_id,
                            vehicle_id ,
                            year_log_text,
                            month_log_text )e on d.parent_id = e.parent_id)g on f.parent_id = g.parent_id""")
