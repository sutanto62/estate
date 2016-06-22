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
                    case when l.tanggal1= 0 then 'standby' when l.tanggal1 < 0 then 'breakdown' else 'available' END tanggal1,
                    case when l.tanggal2= 0 then 'standby' when l.tanggal2 < 0 then 'breakdown' else 'available' END tanggal2,
                    case when l.tanggal3= 0 then 'standby' when l.tanggal3 < 0 then 'breakdown' else 'available' END tanggal3,
                    case when l.tanggal4= 0 then 'standby' when l.tanggal4 < 0 then 'breakdown' else 'available' END tanggal4,
                    case when l.tanggal5= 0 then 'standby' when l.tanggal5 < 0 then 'breakdown' else 'available' END tanggal5,
                    case when l.tanggal6= 0 then 'standby' when l.tanggal6 < 0 then 'breakdown' else 'available' END tanggal6,
                    case when l.tanggal7= 0 then 'standby' when l.tanggal7 < 0 then 'breakdown' else 'available' END tanggal7,
                    case when l.tanggal8= 0 then 'standby' when l.tanggal8 < 0 then 'breakdown' else 'available' END tanggal8,
                    case when l.tanggal9= 0 then 'standby' when l.tanggal9 < 0 then 'breakdown' else 'available' END tanggal9,
                    case when l.tanggal10= 0 then 'standby' when l.tanggal10 < 0 then 'breakdown'else 'available' END tanggal10,
                    case when l.tanggal11= 0 then 'standby' when l.tanggal11 < 0 then 'breakdown' else 'available' END tanggal11,
                    case when l.tanggal12= 0 then 'standby' when l.tanggal12 < 0 then 'breakdown' else 'available' END tanggal12,
                    case when l.tanggal13= 0 then 'standby' when l.tanggal13 < 0 then 'breakdown' else 'available' END tanggal13,
                    case when l.tanggal14= 0 then 'standby' when l.tanggal14 < 0 then 'breakdown' else 'available' END tanggal14,
                    case when l.tanggal15= 0 then 'standby' when l.tanggal15 < 0 then 'breakdown' else 'available' END tanggal15,
                    case when l.tanggal16= 0 then 'standby' when l.tanggal16 < 0 then 'breakdown' else 'available' END tanggal16,
                    case when l.tanggal17= 0 then 'standby' when l.tanggal17 < 0 then 'breakdown' else 'available' END tanggal17,
                    case when l.tanggal18= 0 then 'standby' when l.tanggal18 < 0 then 'breakdown' else 'available' END tanggal18,
                    case when l.tanggal19= 0 then 'standby' when l.tanggal19 < 0 then 'breakdown' else 'available' END tanggal19,
                    case when l.tanggal20= 0 then 'standby' when l.tanggal20 < 0 then 'breakdown' else 'available' END tanggal20,
                    case when l.tanggal21= 0 then 'standby' when l.tanggal21 < 0 then 'breakdown' else 'available' END tanggal21,
                    case when l.tanggal22= 0 then 'standby' when l.tanggal22 < 0 then 'breakdown' else 'available' END tanggal22,
                    case when l.tanggal23= 0 then 'standby' when l.tanggal23 < 0 then 'breakdown' else 'available' END tanggal23,
                    case when l.tanggal24= 0 then 'standby' when l.tanggal24 < 0 then 'breakdown' else 'available' END tanggal24,
                    case when l.tanggal25= 0 then 'standby' when l.tanggal25 < 0 then 'breakdown' else 'available' END tanggal25,
                    case when l.tanggal26= 0 then 'standby' when l.tanggal26 < 0 then 'breakdown' else 'available' END tanggal26,
                    case when l.tanggal27= 0 then 'standby' when l.tanggal27 < 0 then 'breakdown' else 'available' END tanggal27,
                    case when l.tanggal28= 0 then 'standby' when l.tanggal28 < 0 then 'breakdown' else 'available' END tanggal28,
                    case when l.tanggal29= 0 then 'standby' when l.tanggal29 < 0 then 'breakdown' else 'available' END tanggal29,
                    case when l.tanggal30= 0 then 'standby' when l.tanggal30 < 0 then 'breakdown' else 'available' END tanggal30,
                    case when l.tanggal31= 0 then 'standby' when l.tanggal31 < 0 then 'breakdown' else 'available' END tanggal31
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

    _name ='view.calendar.status'
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
        cr.execute("""create or replace view view_calendar_status as
                select
                    row_number() over()id,
                    (k.bulan::text||tahun::text||vehicle_id::text)::Integer date_id,
                    k.bulan,
                    k.tahun,
                    k.vehicle_id,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '1'
                        THEN k.status_day ELSE 0 END) tanggal1,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '2'
                        THEN k.status_day ELSE 0 END) tanggal2,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '3'
                        THEN k.status_day ELSE 0 END) tanggal3,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '4'
                        THEN k.status_day ELSE 0 END) tanggal4,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '5'
                        THEN k.status_day ELSE 0 END) tanggal5,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '6'
                        THEN k.status_day ELSE 0 END) tanggal6,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '7'
                        THEN k.status_day ELSE 0 END) tanggal7,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '8'
                        THEN k.status_day ELSE 0 END) tanggal8,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '9'
                        THEN k.status_day ELSE 0 END) tanggal9,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '10'
                        THEN k.status_day ELSE 0 END) tanggal10,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '11'
                        THEN k.status_day ELSE 0 END) tanggal11,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '12'
                        THEN k.status_day ELSE 0 END) tanggal12,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '13'
                        THEN k.status_day ELSE 0 END) tanggal13,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '14'
                        THEN k.status_day ELSE 0 END) tanggal14,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '15'
                        THEN k.status_day ELSE 0 END) tanggal15,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '16'
                        THEN k.status_day ELSE 0 END) tanggal16,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '17'
                        THEN k.status_day ELSE 0 END) tanggal17,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '18'
                        THEN k.status_day ELSE 0 END) tanggal18,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '19'
                        THEN k.status_day ELSE 0 END) tanggal19,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '20'
                        THEN k.status_day ELSE 0 END) tanggal20,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '21'
                        THEN k.status_day ELSE 0 END) tanggal21,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '22'
                        THEN k.status_day ELSE 0 END) tanggal22,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '23'
                        THEN k.status_day ELSE 0 END) tanggal23,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '24'
                        THEN k.status_day ELSE 0 END) tanggal24,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '25'
                        THEN k.status_day ELSE 0 END) tanggal25,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '26'
                        THEN k.status_day ELSE 0 END) tanggal26,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '27'
                        THEN k.status_day ELSE 0 END) tanggal27,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '28'
                        THEN k.status_day ELSE 0 END) tanggal28,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '29'
                        THEN k.status_day ELSE 0 END) tanggal29,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '30'
                        THEN k.status_day ELSE 0 END) tanggal30,
                    SUM(CASE WHEN TO_CHAR(k.create_date, 'DD') = '31'
                        THEN k.status_day ELSE 0 END) tanggal31 from(
                select
                    b.parent_id,
                    create_date,
                    vehicle_id,
                    bulan,
                    tahun,
                    b.dctype,
                    case when name is null then 1 else 2 end status_day from (
                select
                    create_date,
                    vehicle_id,
                    bulan,
                    tahun,
                    dc_type::text dctype,
                    (bulan::text||tahun::text)::Integer parent_id from (
                select
                    date_trunc('day',etat.date_activity_transport) create_date,
                    vehicle_id, to_char(etat.date_activity_transport,'MM') bulan,
                    to_char(etat.date_activity_transport,'yyyy') tahun,dc_type
                from estate_timesheet_activity_transport etat
                left join (select * from estate_mecanic_timesheet)emt on emt.timesheet_id = etat.id
                 group by date_trunc('day',etat.date_activity_transport), dc_type,vehicle_id, to_char(etat.date_activity_transport,'MM'),to_char(etat.date_activity_transport,'DD'),
                to_char(etat.date_activity_transport,'yyyy')
                )d)b
                left join (
                    select name , (bulan::text||tahun::text)::Integer parent_id from (
                        select name,to_char(date_start,'MM') bulan,
                            to_char(date_start,'yyyy') tahun from master_calendar_effective_date where agendaholiday_id is not null)calendar
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
    bulan = fields.Char()
    tahun = fields.Char()
    hke_ho = fields.Integer()
    hke_non_ho = fields.Integer()
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
    total_day_breakdown = fields.Integer()
    total_day_available = fields.Integer()
    total_day_standby = fields.Integer()

    def init(self, cr):
        cr.execute("""create or replace view view_summary_vehicle_status_detail as
            select
                    status.id,
                    status.bulan,
                    status.tahun,
                    status.parent_id,
                    (status.bulan::text||status.tahun::text||status.vehicle_id::text)::Integer date_id,
                    vehicle_id,hke_ho,hke_non_ho,
                    (tanggal1_status||' , '||tanggal1_hour||' , '||tanggal1_day) tanggal1,
                    (tanggal2_status||' , '||tanggal2_hour||' , '||tanggal2_day) tanggal2,
                    (tanggal3_status||' , '||tanggal3_hour||' , '||tanggal3_day) tanggal3,
                    (tanggal4_status||' , '||tanggal4_hour||' , '||tanggal4_day) tanggal4,
                    (tanggal5_status||' , '||tanggal5_hour||' , '||tanggal5_day) tanggal5,
                    (tanggal6_status||' , '||tanggal6_hour||' , '||tanggal6_day) tanggal6,
                    (tanggal7_status||' , '||tanggal7_hour||' , '||tanggal7_day) tanggal7,
                    (tanggal8_status||' , '||tanggal8_hour||' , '||tanggal8_day) tanggal8,
                    (tanggal9_status||' , '||tanggal9_hour||' , '||tanggal9_day) tanggal9,
                    (tanggal10_status||' , '||tanggal10_hour||' , '||tanggal10_day) tanggal10,
                    (tanggal11_status||' , '||tanggal11_hour||' , '||tanggal11_day) tanggal11,
                    (tanggal12_status||' , '||tanggal12_hour||' , '||tanggal12_day) tanggal12,
                    (tanggal13_status||' , '||tanggal13_hour||' , '||tanggal13_day) tanggal13,
                    (tanggal14_status||' , '||tanggal14_hour||' , '||tanggal14_day) tanggal14,
                    (tanggal15_status||' , '||tanggal15_hour||' , '||tanggal15_day) tanggal15,
                    (tanggal16_status||' , '||tanggal16_hour||' , '||tanggal16_day) tanggal16,
                    (tanggal17_status||' , '||tanggal17_hour||' , '||tanggal17_day) tanggal17,
                    (tanggal18_status||' , '||tanggal18_hour||' , '||tanggal18_day) tanggal18,
                    (tanggal19_status||' , '||tanggal19_hour||' , '||tanggal19_day) tanggal19,
                    (tanggal20_status||' , '||tanggal20_hour||' , '||tanggal20_day) tanggal20,
                    (tanggal21_status||' , '||tanggal21_hour||' , '||tanggal21_day) tanggal21,
                    (tanggal22_status||' , '||tanggal22_hour||' , '||tanggal22_day) tanggal22,
                    (tanggal23_status||' , '||tanggal23_hour||' , '||tanggal23_day) tanggal23,
                    (tanggal24_status||' , '||tanggal24_hour||' , '||tanggal24_day) tanggal24,
                    (tanggal25_status||' , '||tanggal25_hour||' , '||tanggal25_day) tanggal25,
                    (tanggal26_status||' , '||tanggal26_hour||' , '||tanggal26_day) tanggal26,
                    (tanggal27_status||' , '||tanggal27_hour||' , '||tanggal27_day) tanggal27,
                    (tanggal28_status||' , '||tanggal28_hour||' , '||tanggal28_day) tanggal28,
                    (tanggal29_status||' , '||tanggal29_hour||' , '||tanggal29_day) tanggal29,
                    (tanggal30_status||' , '||tanggal30_hour||' , '||tanggal30_day) tanggal30,
                    (tanggal31_status||' , '||tanggal31_hour||' , '||tanggal31_day) tanggal31,
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
                            view_calendar_status vc on vc.date_id = vs.date_id and vc.date_id = vsh.date_id )status
                inner join view_hke_hko hke on status.parent_id = hke.parent_id""")

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

    _name = ''