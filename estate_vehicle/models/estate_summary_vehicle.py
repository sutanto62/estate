from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal

class MasterStructureCostVehicle(models.Model):

    _name = "estate.vehicle.master.cost"
    _description = "Master for cost estate vehicle"


    name=fields.Char()
    vehicle_id = fields.Many2one('fleet.vehicle')
    owner_id = fields.Integer()
    timesheet_id = fields.Many2one('estate.timesheet.activity.transport')
    date_master = fields.Date('Date Master')
    total_wage = fields.Float('Total Cost Wage',digits=(2,2))
    total_fuel = fields.Float('Total CostFuel',digits=(2,2))
    total_oil = fields.Float('Total Cost Oil',digits=(2,2))
    total_sparepart = fields.Float('Total Cost Sparepart',digits=(2,2))
    total_service = fields.Float('Total Cost Sercive',digits=(2,2))
    total_other_cost = fields.Float('Total Other Cost ',digits=(2,2))

    # summary_ids = fields.One2many('v.summary.cost.vehicle','owner_id','Summary Line')

    # wage_ids = fields.One2many()
    fuel_ids = fields.One2many('fleet.vehicle.log.fuel','owner_id')
    # oil_ids = fields.One2many()
    # sparepart_ids = fields.One2many()
    # service_ids = fields.One2many()
    # other_ids = fields.One2many()
class InheritFuel(models.Model):

    _inherit = 'fleet.vehicle.log.fuel'

    owner_id = fields.Integer()

    #onchange owner id
    @api.multi
    @api.onchange('owner_id')
    def _onchange_owner_id(self):
        if self.vehicle_id :
            self.owner_id = self.vehicle_id.id

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
                                'Service' as type_log, vehicle_id,count(*) "count",month_log, year_log, sum(cost_amount) amount
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
                                'Sparepart' as type_log, vehicle_id,count(*) "count",month_log, year_log, sum(amount) amount
                            from (
                                    select fvlf.*,fvc.vehicle_id, date_part('month', fvlf.create_date) month_log, date_part('year', fvlf.create_date) year_log,(fvlf.price_per_unit * fvlf.unit) amount from fleet_vehicle_cost fvc inner join estate_vehicle_log_sparepart fvlf on fvc.id = fvlf.cost_id
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
                                    date_part('month', ts.date_activity_transport) month_log,
                                    date_part('year', ts.date_activity_transport) year_log
                                        from estate_timesheet_activity_transport ts
                                    group by  month_log,year_log ,employee_id
                            )b on a.employee_id = b.employee_id and a.month_log = b.month_log and a.year_log = b.year_log
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
    month_log_text = fields.Text('Month')
    year_log_text = fields.Text('Year')
    total_expense = fields.Float('Amount')
    # parent_id = fields.Text()

    def init(self, cr):
        cr.execute("""create or replace view v_summary_cost_vehicle as
                select (month_log::text||year_log::text||vehicle_id::text)::Integer id,
                    year_log::text year_log_text,
                    to_char(to_timestamp (month_log::text, 'MM'), 'Month') month_log_text,
                    vehicle_id,
                    sum(amount) total_expense
                    from v_summary_cost_vehicle_detail
                    group by year_log,month_log,vehicle_id""")
