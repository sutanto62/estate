from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal
import time
import re


class ViewStatusAvailableVehicle(models.Model):

    _name ='view.status.vehicle.calendar'
    _description = "view for vehicle available in month"
    _auto = False
    _order='vehicle_id'

    id = fields.Integer()
    date_id = fields.Integer()
    bulan = fields.Char()
    tahun = fields.Char()
    vehicle_id = fields.Many2one('fleet.vehicle')
    tanggal1 = fields.Char()
    tanggal2 = fields.Char()
    tanggal3 = fields.Char()
    tanggal4 = fields.Char()
    tanggal5 = fields.Char()
    tanggal6 = fields.Char()
    tanggal7 = fields.Char()
    tanggal8 = fields.Char()
    tanggal9 = fields.Char()
    tanggal10 = fields.Char()
    tanggal11 = fields.Char()
    tanggal12 = fields.Char()
    tanggal13 = fields.Char()
    tanggal14 = fields.Char()
    tanggal15 = fields.Char()
    tanggal16 = fields.Char()
    tanggal17 = fields.Char()
    tanggal18 = fields.Char()
    tanggal19 = fields.Char()
    tanggal20 = fields.Char()
    tanggal21 = fields.Char()
    tanggal22 = fields.Char()
    tanggal23 = fields.Char()
    tanggal24 = fields.Char()
    tanggal25 = fields.Char()
    tanggal26 = fields.Char()
    tanggal27 = fields.Char()
    tanggal28 = fields.Char()
    tanggal29 = fields.Char()
    tanggal30 = fields.Char()
    tanggal31 = fields.Char()

    def init(self, cr):
        cr.execute("""create or replace view view_status_vehicle_calendar as
                select
                    row_number() over()id,
                    (l.bulan::text||tahun::text||vehicle_id::text)::Integer date_id,
                    l.bulan,
                    l.tahun,
                    l.vehicle_id,
                    case when l.tanggal1= 0 then '-' when l.tanggal1 < 0 then 'x' else 'v' END tanggal1,
                    case when l.tanggal2= 0 then '-' when l.tanggal2 < 0 then 'x' else 'v' END tanggal2,
                    case when l.tanggal3= 0 then '-' when l.tanggal3 < 0 then 'x' else 'v' END tanggal3,
                    case when l.tanggal4= 0 then '-' when l.tanggal4 < 0 then 'x' else 'v' END tanggal4,
                    case when l.tanggal5= 0 then '-' when l.tanggal5 < 0 then 'x' else 'v' END tanggal5,
                    case when l.tanggal6= 0 then '-' when l.tanggal6 < 0 then 'x' else 'v' END tanggal6,
                    case when l.tanggal7= 0 then '-' when l.tanggal7 < 0 then 'x' else 'v' END tanggal7,
                    case when l.tanggal8= 0 then '-' when l.tanggal8 < 0 then 'x' else 'v' END tanggal8,
                    case when l.tanggal9= 0 then '-' when l.tanggal9 < 0 then 'x' else 'v' END tanggal9,
                    case when l.tanggal10= 0 then '-' when l.tanggal10 < 0 then 'x'else 'v' END tanggal10,
                    case when l.tanggal11= 0 then '-' when l.tanggal11 < 0 then 'x' else 'v' END tanggal11,
                    case when l.tanggal12= 0 then '-' when l.tanggal12 < 0 then 'x' else 'v' END tanggal12,
                    case when l.tanggal13= 0 then '-' when l.tanggal13 < 0 then 'x' else 'v' END tanggal13,
                    case when l.tanggal14= 0 then '-' when l.tanggal14 < 0 then 'x' else 'v' END tanggal14,
                    case when l.tanggal15= 0 then '-' when l.tanggal15 < 0 then 'x' else 'v' END tanggal15,
                    case when l.tanggal16= 0 then '-' when l.tanggal16 < 0 then 'x' else 'v' END tanggal16,
                    case when l.tanggal17= 0 then '-' when l.tanggal17 < 0 then 'x' else 'v' END tanggal17,
                    case when l.tanggal18= 0 then '-' when l.tanggal18 < 0 then 'x' else 'v' END tanggal18,
                    case when l.tanggal19= 0 then '-' when l.tanggal19 < 0 then 'x' else 'v' END tanggal19,
                    case when l.tanggal20= 0 then '-' when l.tanggal20 < 0 then 'x' else 'v' END tanggal20,
                    case when l.tanggal21= 0 then '-' when l.tanggal21 < 0 then 'x' else 'v' END tanggal21,
                    case when l.tanggal22= 0 then '-' when l.tanggal22 < 0 then 'x' else 'v' END tanggal22,
                    case when l.tanggal23= 0 then '-' when l.tanggal23 < 0 then 'x' else 'v' END tanggal23,
                    case when l.tanggal24= 0 then '-' when l.tanggal24 < 0 then 'x' else 'v' END tanggal24,
                    case when l.tanggal25= 0 then '-' when l.tanggal25 < 0 then 'x' else 'v' END tanggal25,
                    case when l.tanggal26= 0 then '-' when l.tanggal26 < 0 then 'x' else 'v' END tanggal26,
                    case when l.tanggal27= 0 then '-' when l.tanggal27 < 0 then 'x' else 'v' END tanggal27,
                    case when l.tanggal28= 0 then '-' when l.tanggal28 < 0 then 'x' else 'v' END tanggal28,
                    case when l.tanggal29= 0 then '-' when l.tanggal29 < 0 then 'x' else 'v' END tanggal29,
                    case when l.tanggal30= 0 then '-' when l.tanggal30 < 0 then 'x' else 'v' END tanggal30,
                    case when l.tanggal31= 0 then '-' when l.tanggal31 < 0 then 'x' else 'v' END tanggal31
                    from (
                select k.bulan,
                    k.tahun,
                    k.vehicle_id,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '1'
                        THEN k.total_time ELSE 0 END) tanggal1,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '2'
                        THEN k.total_time ELSE 0 END) tanggal2,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '3'
                        THEN k.total_time ELSE 0 END) tanggal3,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '4'
                        THEN k.total_time ELSE 0 END) tanggal4,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '5'
                        THEN k.total_time ELSE 0 END) tanggal5,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '6'
                        THEN k.total_time ELSE 0 END) tanggal6,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '7'
                        THEN k.total_time ELSE 0 END) tanggal7,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '8'
                        THEN k.total_time ELSE 0 END) tanggal8,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '9'
                        THEN k.total_time ELSE 0 END) tanggal9,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '10'
                        THEN k.total_time ELSE 0 END) tanggal10,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '11'
                        THEN k.total_time ELSE 0 END) tanggal11,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '12'
                        THEN k.total_time ELSE 0 END) tanggal12,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '13'
                        THEN k.total_time ELSE 0 END) tanggal13,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '14'
                        THEN k.total_time ELSE 0 END) tanggal14,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '15'
                        THEN k.total_time ELSE 0 END) tanggal15,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '16'
                        THEN k.total_time ELSE 0 END) tanggal16,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '17'
                        THEN k.total_time ELSE 0 END) tanggal17,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '18'
                        THEN k.total_time ELSE 0 END) tanggal18,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '19'
                        THEN k.total_time ELSE 0 END) tanggal19,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '20'
                        THEN k.total_time ELSE 0 END) tanggal20,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '21'
                        THEN k.total_time ELSE 0 END) tanggal21,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '22'
                        THEN k.total_time ELSE 0 END) tanggal22,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '23'
                        THEN k.total_time ELSE 0 END) tanggal23,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '24'
                        THEN k.total_time ELSE 0 END) tanggal24,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '25'
                        THEN k.total_time ELSE 0 END) tanggal25,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '26'
                        THEN k.total_time ELSE 0 END) tanggal26,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '27'
                        THEN k.total_time ELSE 0 END) tanggal27,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '28'
                        THEN k.total_time ELSE 0 END) tanggal28,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '29'
                        THEN k.total_time ELSE 0 END) tanggal29,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '30'
                        THEN k.total_time ELSE 0 END) tanggal30,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '31'
                        THEN k.total_time ELSE 0 END) tanggal31 from(
                select create_date,vehicle_id,bulan,tahun,total_time from(
                select
                    b.parent_id,
                    total_time ,
                    create_date,
                    vehicle_id,
                    bulan,
                    tahun,
                    b.dctype from (
                select
                    total_time ,
                    create_date,
                    vehicle_id,
                    bulan,
                    tahun,
                    dc_type::text dctype,
                    (bulan::text||hari::text||tahun::text)::Integer parent_id from (
                select
                    case when dc_type = '4'
                    then sum(start_time - end_time)
                    when dc_type ='2' or dc_type = '1' or dc_type ='3' or dc_type is null
                    then sum(end_time - start_time)
                    end total_time,
                    date_trunc('day',etat.date_activity_transport) create_date,
                    vehicle_id, to_char(etat.date_activity_transport,'MM') bulan, to_char(etat.date_activity_transport,'DD') hari,
                    to_char(etat.date_activity_transport,'yyyy') tahun,dc_type
                from estate_timesheet_activity_transport etat
                left join (select * from estate_mecanic_timesheet)emt on emt.timesheet_id = etat.id
                 group by date_trunc('day',etat.date_activity_transport), dc_type,vehicle_id, to_char(etat.date_activity_transport,'MM'),to_char(etat.date_activity_transport,'DD'),
                to_char(etat.date_activity_transport,'yyyy')
                )d)b
                left join (
                    select name , (bulan::text||hari::text||tahun::text)::Integer parent_id from (
                        select name,to_char(date_start,'MM') bulan,to_char(date_start,'DD') hari,
                            to_char(date_start,'yyyy') tahun from master_calendar_effective_date where agendaholiday_id is not null)calendar
                )calendars on b.parent_id=calendars.parent_id
                )c)k group by bulan,tahun,vehicle_id
                )l""")

class ViewStatusHourVehicle(models.Model):

    _name ='view.status.vehicle.calendar.hour'
    _description = "view for vehicle available,breakdown,stanby hour in month"
    _auto = False
    _order='vehicle_id'

    id = fields.Integer()
    date_id = fields.Integer()
    bulan = fields.Char()
    tahun = fields.Char()
    vehicle_id = fields.Many2one('fleet.vehicle')
    total_day_breakdown = fields.Float()
    total_day_available = fields.Float()
    total_day_standby = fields.Float()
    tanggal1 = fields.Char()
    tanggal2 = fields.Char()
    tanggal3 = fields.Char()
    tanggal4 = fields.Char()
    tanggal5 = fields.Char()
    tanggal6 = fields.Char()
    tanggal7 = fields.Char()
    tanggal8 = fields.Char()
    tanggal9 = fields.Char()
    tanggal10 = fields.Char()
    tanggal11 = fields.Char()
    tanggal12 = fields.Char()
    tanggal13 = fields.Char()
    tanggal14 = fields.Char()
    tanggal15 = fields.Char()
    tanggal16 = fields.Char()
    tanggal17 = fields.Char()
    tanggal18 = fields.Char()
    tanggal19 = fields.Char()
    tanggal20 = fields.Char()
    tanggal21 = fields.Char()
    tanggal22 = fields.Char()
    tanggal23 = fields.Char()
    tanggal24 = fields.Char()
    tanggal25 = fields.Char()
    tanggal26 = fields.Char()
    tanggal27 = fields.Char()
    tanggal28 = fields.Char()
    tanggal29 = fields.Char()
    tanggal30 = fields.Char()
    tanggal31 = fields.Char()

    def init(self, cr):
        cr.execute("""create or replace view view_status_vehicle_calendar_hour as
                select
                    row_number() over()id,
                    (k.bulan::text||tahun::text||vehicle_id::text)::Integer date_id,
                    k.bulan,
                    k.tahun,
                    k.vehicle_id,
                    count(*)filter(where total_time < 0) total_day_breakdown,
                    count (*)filter(where total_time > 0)total_day_available,
                    case when ((select to_char(now(),'MM')::integer) = k.bulan::integer and (select to_char(now(),'YYYY')::integer) = k.tahun::integer)
                    then
                        (select to_char(now(),'DD')::integer) - count(*)filter(where total_time < 0) - count (*)filter(where total_time > 0)
                    else
                        (SELECT DATE_PART('days',DATE_TRUNC('month', (select to_date('01/'||k.bulan||'/'||k.tahun, 'DD/MM/YYYY')))+'1 MONTH'::INTERVAL-'1 DAY'::INTERVAL)) - count(*)filter(where total_time < 0) - count (*)filter(where total_time > 0)
                    END total_day_standby,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '1'
                        THEN k.total_time ELSE 0 END) tanggal1,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '2'
                        THEN k.total_time ELSE 0 END) tanggal2,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '3'
                        THEN k.total_time ELSE 0 END) tanggal3,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '4'
                        THEN k.total_time ELSE 0 END) tanggal4,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '5'
                        THEN k.total_time ELSE 0 END) tanggal5,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '6'
                        THEN k.total_time ELSE 0 END) tanggal6,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '7'
                        THEN k.total_time ELSE 0 END) tanggal7,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '8'
                        THEN k.total_time ELSE 0 END) tanggal8,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '9'
                        THEN k.total_time ELSE 0 END) tanggal9,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '10'
                        THEN k.total_time ELSE 0 END) tanggal10,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '11'
                        THEN k.total_time ELSE 0 END) tanggal11,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '12'
                        THEN k.total_time ELSE 0 END) tanggal12,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '13'
                        THEN k.total_time ELSE 0 END) tanggal13,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '14'
                        THEN k.total_time ELSE 0 END) tanggal14,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '15'
                        THEN k.total_time ELSE 0 END) tanggal15,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '16'
                        THEN k.total_time ELSE 0 END) tanggal16,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '17'
                        THEN k.total_time ELSE 0 END) tanggal17,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '18'
                        THEN k.total_time ELSE 0 END) tanggal18,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '19'
                        THEN k.total_time ELSE 0 END) tanggal19,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '20'
                        THEN k.total_time ELSE 0 END) tanggal20,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '21'
                        THEN k.total_time ELSE 0 END) tanggal21,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '22'
                        THEN k.total_time ELSE 0 END) tanggal22,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '23'
                        THEN k.total_time ELSE 0 END) tanggal23,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '24'
                        THEN k.total_time ELSE 0 END) tanggal24,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '25'
                        THEN k.total_time ELSE 0 END) tanggal25,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '26'
                        THEN k.total_time ELSE 0 END) tanggal26,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '27'
                        THEN k.total_time ELSE 0 END) tanggal27,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '28'
                        THEN k.total_time ELSE 0 END) tanggal28,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '29'
                        THEN k.total_time ELSE 0 END) tanggal29,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '30'
                        THEN k.total_time ELSE 0 END) tanggal30,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '31'
                        THEN k.total_time ELSE 0 END) tanggal31 from(
                select create_date,vehicle_id,hari,bulan,tahun,total_time from(
                select
                    b.parent_id,
                    total_time ,
                    create_date,
                    vehicle_id,hari,
                    bulan,
                    tahun,
                    b.dctype
                    from (
                select
                    total_time ,
                    create_date,
                    vehicle_id,hari,
                    bulan,
                    tahun,
                    dc_type::text dctype,
                    (bulan::text||hari::text||tahun::text)::Integer parent_id from (
                select
                    case when dc_type = '4'
                    then sum(start_time - end_time)
                    when dc_type ='2' or dc_type = '1' or dc_type ='3' or dc_type is null
                    then sum(end_time - start_time)
                    end total_time,
                    date_trunc('day',etat.date_activity_transport) create_date,
                    vehicle_id, to_char(etat.date_activity_transport,'MM') bulan, to_char(etat.date_activity_transport,'DD') hari,
                    to_char(etat.date_activity_transport,'yyyy') tahun,dc_type
                from estate_timesheet_activity_transport etat
                left join (select * from estate_mecanic_timesheet)emt on emt.timesheet_id = etat.id
                 group by date_trunc('day',etat.date_activity_transport), dc_type,vehicle_id, to_char(etat.date_activity_transport,'MM'),to_char(etat.date_activity_transport,'DD'),
                to_char(etat.date_activity_transport,'yyyy')
                )d
                )b
                )c
                )k group by bulan,tahun,vehicle_id""")


class ViewStatusDayVehicle(models.Model):

    _name ='view.calendar.status.detail'
    _description = "view for status calendar in month"
    _auto = False
    _order='vehicle_id'

    id = fields.Integer()
    date_id = fields.Integer()
    bulan = fields.Char()
    tahun = fields.Char()
    vehicle_id = fields.Many2one('fleet.vehicle')
    tanggal1 = fields.Char()
    tanggal2 = fields.Char()
    tanggal3 = fields.Char()
    tanggal4 = fields.Char()
    tanggal5 = fields.Char()
    tanggal6 = fields.Char()
    tanggal7 = fields.Char()
    tanggal8 = fields.Char()
    tanggal9 = fields.Char()
    tanggal10 = fields.Char()
    tanggal11 = fields.Char()
    tanggal12 = fields.Char()
    tanggal13 = fields.Char()
    tanggal14 = fields.Char()
    tanggal15 = fields.Char()
    tanggal16 = fields.Char()
    tanggal17 = fields.Char()
    tanggal18 = fields.Char()
    tanggal19 = fields.Char()
    tanggal20 = fields.Char()
    tanggal21 = fields.Char()
    tanggal22 = fields.Char()
    tanggal23 = fields.Char()
    tanggal24 = fields.Char()
    tanggal25 = fields.Char()
    tanggal26 = fields.Char()
    tanggal27 = fields.Char()
    tanggal28 = fields.Char()
    tanggal29 = fields.Char()
    tanggal30 = fields.Char()
    tanggal31 = fields.Char()

    def init(self, cr):
        cr.execute("""create or replace view view_calendar_status_detail as
                select
                    row_number() over()id,
                    (k.bulan::text||tahun::text||vehicle_id::text)::Integer date_id,
                    k.bulan,
                    k.tahun,
                    k.vehicle_id,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '1'
                        THEN k.status_day ELSE 0 END) tanggal1,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '2'
                        THEN k.status_day ELSE 0 END) tanggal2,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '3'
                        THEN k.status_day ELSE 0 END) tanggal3,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '4'
                        THEN k.status_day ELSE 0 END) tanggal4,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '5'
                        THEN k.status_day ELSE 0 END) tanggal5,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '6'
                        THEN k.status_day ELSE 0 END) tanggal6,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '7'
                        THEN k.status_day ELSE 0 END) tanggal7,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '8'
                        THEN k.status_day ELSE 0 END) tanggal8,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '9'
                        THEN k.status_day ELSE 0 END) tanggal9,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '10'
                        THEN k.status_day ELSE 0 END) tanggal10,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '11'
                        THEN k.status_day ELSE 0 END) tanggal11,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '12'
                        THEN k.status_day ELSE 0 END) tanggal12,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '13'
                        THEN k.status_day ELSE 0 END) tanggal13,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '14'
                        THEN k.status_day ELSE 0 END) tanggal14,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '15'
                        THEN k.status_day ELSE 0 END) tanggal15,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '16'
                        THEN k.status_day ELSE 0 END) tanggal16,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '17'
                        THEN k.status_day ELSE 0 END) tanggal17,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '18'
                        THEN k.status_day ELSE 0 END) tanggal18,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '19'
                        THEN k.status_day ELSE 0 END) tanggal19,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '20'
                        THEN k.status_day ELSE 0 END) tanggal20,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '21'
                        THEN k.status_day ELSE 0 END) tanggal21,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '22'
                        THEN k.status_day ELSE 0 END) tanggal22,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '23'
                        THEN k.status_day ELSE 0 END) tanggal23,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '24'
                        THEN k.status_day ELSE 0 END) tanggal24,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '25'
                        THEN k.status_day ELSE 0 END) tanggal25,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '26'
                        THEN k.status_day ELSE 0 END) tanggal26,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '27'
                        THEN k.status_day ELSE 0 END) tanggal27,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '28'
                        THEN k.status_day ELSE 0 END) tanggal28,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '29'
                        THEN k.status_day ELSE 0 END) tanggal29,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '30'
                        THEN k.status_day ELSE 0 END) tanggal30,
                    MAX(CASE WHEN TO_CHAR(k.create_date, 'DD') = '31'
                        THEN k.status_day ELSE 0 END) tanggal31 from(
                    select
                        b.parent_id,
                        create_date,
                        vehicle_id,
                        bulan,
                        tahun,
                        b.dctype,
                        case
                        when role = '2' then 2
                        else 1 end status_day
                    from (
                        select
                            create_date,
                            vehicle_id,
                            bulan,
                            tahun,
                            dc_type::text dctype,
                            (bulan::text||hari::text||tahun::text)::Integer parent_id
                        from (
                            select
                                date_trunc('day',etat.date_activity_transport) create_date,
                                vehicle_id, to_char(etat.date_activity_transport,'MM') bulan,to_char(etat.date_activity_transport,'DD') hari,
                                to_char(etat.date_activity_transport,'yyyy') tahun,dc_type
                            from
                                estate_timesheet_activity_transport etat
                                left join estate_mecanic_timesheet emt
                                on emt.timesheet_id = etat.id
                                group by
                                    date_trunc('day',etat.date_activity_transport),
                                    dc_type,vehicle_id, to_char(etat.date_activity_transport,'MM'),
                                    to_char(etat.date_activity_transport,'yyyy'),to_char(etat.date_activity_transport,'DD')
                            )d
                        )b
                        left join (
                        select
                            name ,role, (bulan::text||hari::text||tahun::text)::Integer parent_id
                        from (
                                select
                                    name,to_char(date_start,'MM') bulan,
                                    to_char(date_start,'DD') hari,role,
                                    to_char(date_start,'yyyy') tahun
                                from
                                    master_calendar_effective_date
                                where
                                    agendaholiday_id is not null and role='2')c
                                    )calendars on b.parent_id=calendars.parent_id
                                    )k group by bulan,tahun,vehicle_id,status_day""")

class ViewSummaryVehicleStatusDetail(models.Model):

    _name ='view.summary.vehicle.status.detail'
    _description = "view for status detail in month"
    _auto = False
    _order='bulan'

    id = fields.Integer()
    date_id = fields.Integer()
    parent_id = fields.Integer()
    month_log_text = fields.Char()
    year_log_text = fields.Char()
    hke_ho = fields.Integer()
    hke_non_ho = fields.Integer()
    vehicle_id = fields.Many2one('fleet.vehicle')
    date1 = fields.Char()
    date2 = fields.Char()
    date3 = fields.Char()
    date4 = fields.Char()
    date5 = fields.Char()
    date6 = fields.Char()
    date7 = fields.Char()
    date8 = fields.Char()
    date9 = fields.Char()
    date10 = fields.Char()
    date11 = fields.Char()
    date12 = fields.Char()
    date13 = fields.Char()
    date14 = fields.Char()
    date15 = fields.Char()
    date16 = fields.Char()
    date17 = fields.Char()
    date18 = fields.Char()
    date19 = fields.Char()
    date20 = fields.Char()
    date21 = fields.Char()
    date22 = fields.Char()
    date23 = fields.Char()
    date24 = fields.Char()
    date25 = fields.Char()
    date26 = fields.Char()
    date27 = fields.Char()
    date28 = fields.Char()
    date29 = fields.Char()
    date30 = fields.Char()
    date31 = fields.Char()
    total_day_breakdown = fields.Integer()
    total_day_available = fields.Integer()
    total_day_standby = fields.Integer()
    total_downtime = fields.Float()

    def init(self, cr):
        cr.execute("""create or replace view view_summary_vehicle_status_detail as
                select * , ((total_day_breakdown/hke_non_ho)*100) total_downtime from(
                    select
                        status.id,
                        status.bulan as month_log_text,
                        status.tahun as year_log_text,
                        status.parent_id,
                        (status.bulan::text||status.tahun::text||status.vehicle_id::text)::Integer date_id,
                        vehicle_id,hke_ho,hke_non_ho,
                        case when tanggal1_status = '-' then tanggal1_status else (tanggal1_status||','||tanggal1_hour||','||tanggal1_day) end date1,
                        case when tanggal2_status = '-' then tanggal2_status else (tanggal2_status||','||tanggal2_hour||','||tanggal2_day) end date2,
                        case when tanggal3_status = '-' then tanggal3_status else (tanggal3_status||','||tanggal3_hour||','||tanggal3_day) end date3,
                        case when tanggal4_status = '-' then tanggal4_status else (tanggal4_status||','||tanggal4_hour||','||tanggal4_day) end date4,
                        case when tanggal5_status = '-' then tanggal5_status else (tanggal5_status||','||tanggal5_hour||','||tanggal5_day) end date5,
                        case when tanggal6_status = '-' then tanggal6_status else (tanggal6_status||','||tanggal6_hour||','||tanggal6_day) end date6,
                        case when tanggal7_status = '-' then tanggal7_status else (tanggal7_status||','||tanggal7_hour||','||tanggal7_day) end date7,
                        case when tanggal8_status = '-' then tanggal8_status else (tanggal8_status||','||tanggal8_hour||','||tanggal8_day) end date8,
                        case when tanggal9_status = '-' then tanggal9_status else (tanggal9_status||','||tanggal9_hour||','||tanggal9_day) end date9,
                        case when tanggal10_status = '-' then tanggal10_status else (tanggal10_status||','||tanggal10_hour||','||tanggal10_day) end date10,
                        case when tanggal11_status = '-' then tanggal11_status else (tanggal11_status||','||tanggal11_hour||','||tanggal11_day) end date11,
                        case when tanggal12_status = '-' then tanggal12_status else (tanggal12_status||','||tanggal12_hour||','||tanggal12_day) end date12,
                        case when tanggal13_status = '-' then tanggal13_status else (tanggal13_status||','||tanggal13_hour||','||tanggal13_day) end date13,
                        case when tanggal14_status = '-' then tanggal14_status else (tanggal14_status||','||tanggal14_hour||','||tanggal14_day) end date14,
                        case when tanggal15_status = '-' then tanggal15_status else (tanggal15_status||','||tanggal15_hour||','||tanggal15_day) end date15,
                        case when tanggal16_status = '-' then tanggal16_status else (tanggal16_status||','||tanggal16_hour||','||tanggal16_day) end date16,
                        case when tanggal17_status = '-' then tanggal17_status else (tanggal17_status||','||tanggal17_hour||','||tanggal17_day) end date17,
                        case when tanggal18_status = '-' then tanggal18_status else (tanggal18_status||','||tanggal18_hour||','||tanggal18_day) end date18,
                        case when tanggal19_status = '-' then tanggal19_status else (tanggal19_status||','||tanggal19_hour||','||tanggal19_day) end date19,
                        case when tanggal20_status = '-' then tanggal20_status else (tanggal20_status||','||tanggal20_hour||','||tanggal20_day) end date20,
                        case when tanggal21_status = '-' then tanggal21_status else (tanggal21_status||','||tanggal21_hour||','||tanggal21_day) end date21,
                        case when tanggal22_status = '-' then tanggal22_status else (tanggal22_status||','||tanggal22_hour||','||tanggal22_day) end date22,
                        case when tanggal23_status = '-' then tanggal23_status else (tanggal23_status||','||tanggal23_hour||','||tanggal23_day) end date23,
                        case when tanggal24_status = '-' then tanggal24_status else (tanggal24_status||','||tanggal24_hour||','||tanggal24_day) end date24,
                        case when tanggal25_status = '-' then tanggal25_status else (tanggal25_status||','||tanggal25_hour||','||tanggal25_day) end date25,
                        case when tanggal26_status = '-' then tanggal26_status else (tanggal26_status||','||tanggal26_hour||','||tanggal26_day) end date26,
                        case when tanggal27_status = '-' then tanggal27_status else (tanggal27_status||','||tanggal27_hour||','||tanggal27_day) end date27,
                        case when tanggal28_status = '-' then tanggal28_status else (tanggal28_status||','||tanggal28_hour||','||tanggal28_day) end date28,
                        case when tanggal29_status = '-' then tanggal29_status else (tanggal29_status||','||tanggal29_hour||','||tanggal29_day) end date29,
                        case when tanggal30_status = '-' then tanggal30_status else (tanggal30_status||','||tanggal30_hour||','||tanggal30_day) end date30,
                        case when tanggal31_status = '-' then tanggal31_status else (tanggal31_status||','||tanggal31_hour||','||tanggal31_day) end date31,
                        total_day_breakdown,total_day_available,total_day_standby
                        from(
                            select
                            row_number() over()id,
                            (vs.bulan::text||vs.tahun::text)::Integer parent_id,
                            vs.date_id,vs.bulan,vs.tahun,vs.vehicle_id,vsh.total_day_breakdown,vsh.total_day_available,vsh.total_day_standby,
                            vs.tanggal1 tanggal1_status,vsh.tanggal1 tanggal1_hour,vc.tanggal1 tanggal1_day,
                            vs.tanggal2 tanggal2_status,vsh.tanggal2 tanggal2_hour,vc.tanggal2 tanggal2_day,
                            vs.tanggal3 tanggal3_status,vsh.tanggal3 tanggal3_hour,vc.tanggal3 tanggal3_day,
                            vs.tanggal4 tanggal4_status,vsh.tanggal4 tanggal4_hour,vc.tanggal4 tanggal4_day,
                            vs.tanggal5 tanggal5_status,vsh.tanggal5 tanggal5_hour,vc.tanggal5 tanggal5_day,
                            vs.tanggal6 tanggal6_status,vsh.tanggal6 tanggal6_hour,vc.tanggal6 tanggal6_day,
                            vs.tanggal7 tanggal7_status,vsh.tanggal7 tanggal7_hour,vc.tanggal7 tanggal7_day,
                            vs.tanggal8 tanggal8_status,vsh.tanggal8 tanggal8_hour,vc.tanggal8 tanggal8_day,
                            vs.tanggal9 tanggal9_status,vsh.tanggal9 tanggal9_hour,vc.tanggal9 tanggal9_day,
                            vs.tanggal10 tanggal10_status,vsh.tanggal10 tanggal10_hour,vc.tanggal10 tanggal10_day,
                            vs.tanggal11 tanggal11_status,vsh.tanggal11 tanggal11_hour,vc.tanggal11 tanggal11_day,
                            vs.tanggal12 tanggal12_status,vsh.tanggal12 tanggal12_hour,vc.tanggal12 tanggal12_day,
                            vs.tanggal13 tanggal13_status,vsh.tanggal13 tanggal13_hour,vc.tanggal13 tanggal13_day,
                            vs.tanggal14 tanggal14_status,vsh.tanggal14 tanggal14_hour,vc.tanggal14 tanggal14_day,
                            vs.tanggal15 tanggal15_status,vsh.tanggal15 tanggal15_hour,vc.tanggal15 tanggal15_day,
                            vs.tanggal16 tanggal16_status,vsh.tanggal16 tanggal16_hour,vc.tanggal16 tanggal16_day,
                            vs.tanggal17 tanggal17_status,vsh.tanggal17 tanggal17_hour,vc.tanggal17 tanggal17_day,
                            vs.tanggal18 tanggal18_status,vsh.tanggal18 tanggal18_hour,vc.tanggal18 tanggal18_day,
                            vs.tanggal19 tanggal19_status,vsh.tanggal19 tanggal19_hour,vc.tanggal19 tanggal19_day,
                            vs.tanggal20 tanggal20_status,vsh.tanggal20 tanggal20_hour,vc.tanggal20 tanggal20_day,
                            vs.tanggal21 tanggal21_status,vsh.tanggal21 tanggal21_hour,vc.tanggal21 tanggal21_day,
                            vs.tanggal22 tanggal22_status,vsh.tanggal22 tanggal22_hour,vc.tanggal22 tanggal22_day,
                            vs.tanggal23 tanggal23_status,vsh.tanggal23 tanggal23_hour,vc.tanggal23 tanggal23_day,
                            vs.tanggal24 tanggal24_status,vsh.tanggal24 tanggal24_hour,vc.tanggal24 tanggal24_day,
                            vs.tanggal25 tanggal25_status,vsh.tanggal25 tanggal25_hour,vc.tanggal25 tanggal25_day,
                            vs.tanggal26 tanggal26_status,vsh.tanggal26 tanggal26_hour,vc.tanggal26 tanggal26_day,
                            vs.tanggal27 tanggal27_status,vsh.tanggal27 tanggal27_hour,vc.tanggal27 tanggal27_day,
                            vs.tanggal28 tanggal28_status,vsh.tanggal28 tanggal28_hour,vc.tanggal28 tanggal28_day,
                            vs.tanggal29 tanggal29_status,vsh.tanggal29 tanggal29_hour,vc.tanggal29 tanggal29_day,
                            vs.tanggal30 tanggal30_status,vsh.tanggal30 tanggal30_hour,vc.tanggal30 tanggal30_day,
                            vs.tanggal31 tanggal31_status,vsh.tanggal31 tanggal31_hour,vc.tanggal31 tanggal31_day
                            from
                                view_status_vehicle_calendar vs
                                inner join
                                view_status_vehicle_calendar_hour vsh
                                on vs.date_id = vsh.date_id
                                inner join
                                view_calendar_status_detail vc on vc.date_id = vs.date_id and vc.date_id = vsh.date_id )status
                    inner join view_hke_hko hke on status.parent_id = hke.parent_id)a""")

class ViewSummaryVehicleStatusAvailable(models.Model):

    _name ='view_hke_hko'
    _description = "view for day of week"
    _auto = False
    _order='bulan'

    id = fields.Integer()
    parent_id = fields.Integer()
    bulan = fields.Char()
    tahun = fields.Char()
    hke_ho= fields.Integer()
    hke_non_ho = fields.Integer()

    def init(self, cr):
        cr.execute("""create or replace view view_hke_hko as
                select
                row_number() over()id,
                vcs.bulan,
                vcs.tahun,
                (vcs.bulan::text||vcs.tahun::text)::integer parent_id,
                (
                SELECT
                DATE_PART(
                'days',
                DATE_TRUNC(
                'month', (select to_date('01/'||vcs.bulan||'/'||vcs.tahun, 'DD/MM/YYYY')))
                +
                '1 MONTH'::INTERVAL
                -
                '1 DAY'::INTERVAL
                ))
                -
                (select count(*) from master_calendar_effective_date
                where
                    to_char(date_start, 'MM')::integer = 6 and
                    to_char(date_start, 'YYYY')::integer = 2016 and
                    role = '1'
                )hke_ho,
                (
                SELECT
                DATE_PART(
                'days',
                DATE_TRUNC(
                'month', (select to_date('01/'||vcs.bulan||'/'||vcs.tahun, 'DD/MM/YYYY')))
                +
                '1 MONTH'::INTERVAL
                -
                '1 DAY'::INTERVAL
                ))
                -
                (select count(*) from master_calendar_effective_date
                where
                    to_char(date_start, 'MM')::integer = vcs.bulan::integer and
                    to_char(date_start, 'YYYY')::integer = vcs.tahun::integer and
                    role = '2'
                )hke_non_ho
                from (select bulan, tahun from view_calendar_status group by bulan, tahun) vcs""")

class ViewSummaryVehicleStatus(models.Model):

    _name = 'view.summary.vehicle.available'
    _description = "view for result total available vehicle"
    _auto = False
    _order="year_log_text,month asc"

    id = fields.Integer()
    date_id = fields.Integer()
    parent_id = fields.Integer('Parent_id')
    month_log_text = fields.Char('Month')
    month = fields.Integer()
    year_log_text = fields.Char('Year')
    hke_ho = fields.Integer('Effective Day HO')
    hke_non_ho = fields.Integer('Effective Day Non HO')
    sbi_total_day_hke = fields.Integer('Year To Date Effective Day')
    status_vehicle_ids = fields.One2many('view.summary.vehicle.status.detail','parent_id','status Vehicle')
    vehicle_id = fields.Many2one('fleet.vehicle')
    date1 = fields.Char()
    date2 = fields.Char()
    date3 = fields.Char()
    date4 = fields.Char()
    date5 = fields.Char()
    date6 = fields.Char()
    date7 = fields.Char()
    date8 = fields.Char()
    date9 = fields.Char()
    date10 = fields.Char()
    date11 = fields.Char()
    date12 = fields.Char()
    date13 = fields.Char()
    date14 = fields.Char()
    date15 = fields.Char()
    date16 = fields.Char()
    date17 = fields.Char()
    date18 = fields.Char()
    date19 = fields.Char()
    date20 = fields.Char()
    date21 = fields.Char()
    date22 = fields.Char()
    date23 = fields.Char()
    date24 = fields.Char()
    date25 = fields.Char()
    date26 = fields.Char()
    date27 = fields.Char()
    date28 = fields.Char()
    date29 = fields.Char()
    date30 = fields.Char()
    date31 = fields.Char()
    total_day_breakdown = fields.Integer('Month to Date Breakdown')
    sbi_total_day_breakdown = fields.Integer('Year To Date Breakdown')
    total_day_available = fields.Integer('Month To Date Available')
    sbi_total_day_available = fields.Integer('Year To Date Available')
    total_day_standby = fields.Integer('Month to Date Standby')
    sbi_total_day_standby = fields.Integer('Year To Date Standby')
    total_downtime = fields.Float('Total Downtime')


    def init(self, cr):
        cr.execute("""create or replace view view_summary_vehicle_available as
                select
                    k.id,
                    (to_char(to_timestamp (k.month_log_text::text, 'MM'), 'Month')) as month_log_text,
                    k.year_log_text ,
                    k.month_log_text::integer as month,
                    k.parent_id,
                    k.date_id,
                    vehicle_id,hke_ho,hke_non_ho,
                    date1,
                    date2,
                    date3,
                    date4,
                    date5,
                    date6,
                    date7,
                    date8,
                    date9,
                    date10,
                    date11,
                    date12,
                    date13,
                    date14,
                    date15,
                    date16,
                    date17,
                    date18,
                    date19,
                    date20,
                    date21,
                    date22,
                    date23,
                    date24,
                    date25,
                    date26,
                    date27,
                    date28,
                    date29,
                    date30,
                    date31,
                    total_day_breakdown,total_day_available,total_day_standby,total_downtime,
                    somefuncname(k.month_log_text::integer,k.year_log_text::integer,k.vehicle_id,1) sbi_total_day_breakdown,
                    somefuncname(k.month_log_text::integer,k.year_log_text::integer,k.vehicle_id,2) sbi_total_day_available,
                    somefuncname(k.month_log_text::integer,k.year_log_text::integer,k.vehicle_id,3) sbi_total_day_standby,
                    somefuncname(k.month_log_text::integer,k.year_log_text::Integer,k.vehicle_id,4) sbi_total_day_hke
                from view_summary_vehicle_status_detail	k	order by month asc""")