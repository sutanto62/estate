from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal


class CreateFunctionName(models.Model):

    _name = "somefuncname"
    _description = "Function to Create Name"
    _auto = False

    def init(self, cr):
        cr.execute("""CREATE OR REPLACE FUNCTION somefuncname(i_bulan int,i_tahun int,i_vehicle_id int, i_status int)
                    RETURNS int LANGUAGE plpgsql AS $BODY$
                    DECLARE
                        v_total_day_breakdown int;
                    BEGIN
                        select
                            case when i_status = 1 then --HO
                                sum(total_day_breakdown)
                            when i_status = 2 then
                                sum(total_day_available)
                            when i_status = 3 then
                                sum(total_day_standby)
                            when i_status = 4 then
                                sum(hke_non_ho)
                            end into v_total_day_breakdown
                        from
                            view_summary_vehicle_status_detail v
                        where
                            v.month_log_text::integer <= i_bulan
                            and
                            v.year_log_text::integer = i_tahun
                            and
                            v.vehicle_id = i_vehicle_id;
                      RETURN v_total_day_breakdown ;
                    END
                    $BODY$;
                   """)

 # generate holiday peryear

class CreateFunctionGenerateHolidayPeryear(models.Model):

    _name = "insert.range.into.calendar"
    _description = "Function to Generate Holiday Per Year"
    _auto = False

    def init(self, cr):
        cr.execute("""CREATE OR REPLACE FUNCTION insert_range_into_calendar(from_date date, to_date date)
                  RETURNS void AS
                $BODY$

                DECLARE
                    this_date date := from_date;
                BEGIN

                    while (this_date <= to_date) LOOP
                        if (select extract(dow from this_date)) = 0 then --'Sun'
                            delete from public.master_calendar_effective_date where to_char(date_start,'DD/MM/YYYY') = to_char(this_date,'DD/MM/YYYY') and state = 'x';
                            INSERT INTO public.master_calendar_effective_date
                            (id, create_uid, create_date, "name", write_uid, write_date, date_stop, date_start, state, agendaholiday_id, role)
                            VALUES(nextval('master_calendar_effective_date_id_seq'::regclass), 1, now(), 'Weekend', 1, now(), this_date, this_date, 'x', 2, '1');
                            INSERT INTO public.master_calendar_effective_date
                            (id, create_uid, create_date, "name", write_uid, write_date, date_stop, date_start, state, agendaholiday_id, role)
                            VALUES(nextval('master_calendar_effective_date_id_seq'::regclass), 1, now(), 'Weekend Non HO', 1, now(), this_date, this_date, 'x', 2, '2');
                        elseif (select extract(dow from this_date)) = 6 then --'Sat'
                            delete from public.master_calendar_effective_date where to_char(date_start,'DD/MM/YYYY') = to_char(this_date,'DD/MM/YYYY') and state = 'x';
                            INSERT INTO public.master_calendar_effective_date
                            (id, create_uid, create_date, "name", write_uid, write_date, date_stop, date_start, state, agendaholiday_id, role)
                            VALUES(nextval('master_calendar_effective_date_id_seq'::regclass), 1, now(), 'Weekend', 1, now(), this_date, this_date, 'x', 3, '1');
                        end if;
                        this_date = this_date + interval '1 day';
                    end loop;
                END;
                $BODY$
                  LANGUAGE plpgsql VOLATILE
                  COST 100;
                   """)

class CountMultiplyOdometer(models.Model):

    _name = "count.multiply.odometer"
    _description = "Function to Jobs Sheduling"
    _auto = False

    def init(self, cr):
        cr.execute("""CREATE OR REPLACE FUNCTION count_multiply_odometer(i_odometer integer, i_odometer_current integer)
                      RETURNS integer AS
                    $BODY$
                    declare
                        count_multiply integer;
                    begin
                        count_multiply = 1;

                        while (count_multiply * i_odometer < i_odometer_current) loop
                            count_multiply = count_multiply + 1;
                        end loop;

                        return count_multiply;
                    end;
                    $BODY$
                      LANGUAGE plpgsql VOLATILE
                      COST 100;
                   """)

class CreatemoPreventive(models.Model):

    _name = "create.mo.preventive"
    _description = "Function to Jobs Sheduling"
    _auto = False

    def init(self, cr):
        cr.execute("""CREATE OR REPLACE FUNCTION create_mo_preventive()
                  RETURNS boolean AS
                $BODY$
                declare
                    v_seq_id integer;
                    v_name_mro text;
                    v_vpo RECORD;
                begin

                    FOR v_vpo IN
                        select
                            fleet_id,
                            asset_id,
                            odometer,
                            odometer_current,
                            count_multiply,
                            odometer_remain,
                            odometer_threshold
                        from
                            vehicle_preventive_odometer
                        where
                            odometer_remain < odometer_threshold
                    LOOP
                        select nextval('mro_order_id_seq') into v_seq_id;
                        select substring('MRO00000' from 0 for char_length('MRO00000')-char_length(v_seq_id::text)+1)||v_seq_id into v_name_mro;
                        INSERT INTO public.mro_order
                            (
                                id,
                                origin,
                                create_date,
                                write_uid,
                                asset_id,
                                create_uid,
                                company_id,
                                state,
                                maintenance_type,
                                description,
                                write_date,
                                "name",
                                date_planned,
                                date_execution,
                                date_scheduled,
                                type_service,
                                code_id
                            )
                        VALUES
                            (
                                v_seq_id,
                                v_vpo.odometer||'-'|| v_vpo.odometer_threshold,
                                now(),
                                1,
                                v_vpo.asset_id,
                                1,
                                1,
                                'draft',
                                'pm',
                                v_vpo.odometer||'-'|| v_vpo.odometer_threshold,
                                now(),
                                v_name_mro,
                                now(),
                                now(),
                                now(),
                                '1',
                                11
                            );
                    END LOOP;

                    return true;
                end;
                $BODY$
                  LANGUAGE plpgsql VOLATILE
                  COST 100;""")



