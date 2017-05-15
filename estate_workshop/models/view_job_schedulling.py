from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal



class ViewVehiclePreventiveOdometer(models.Model):

    _name = "vehicle.preventive.odometer"
    _description = "Function to Vehicle Preventive Odometer "
    _auto = False

    def init(self, cr):
        cr.execute("""CREATE OR REPLACE FUNCTION function_get_totalday_breakdown(i_month_log_text int,i_year_log_text int,i_vehicle_id int, i_status int)
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
                            v.month_log_text::integer <= i_month_log_text
                            and
                            v.year_log_text::integer = i_year_log_text
                            and
                            v.vehicle_id = i_vehicle_id;
                      RETURN v_total_day_breakdown ;
                    END
                    $BODY$;
                   """)

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

        cr.execute("""CREATE OR REPLACE VIEW vehicle_preventive_odometer AS
             SELECT mul_odo.fleet_id,
                    mul_odo.asset_id,
                    mul_odo.odometer,
                    mul_odo.odometer_current,
                    mul_odo.count_multiply,
                    mul_odo.odometer_remain,
                    mul_odo.odometer_threshold
                   FROM ( SELECT row_number() OVER (PARTITION BY b.fleet_id ORDER BY b.multiple_odo, b.count_multiply) AS idx,
                            b.fleet_id,
                            b.asset_id,
                            b.odometer,
                            b.odometer_current,
                            b.multiple_odo,
                            b.count_multiply,
                            b.odometer_remain,
                            b.odometer_threshold
                           FROM ( SELECT a.fleet_id,
                                    a.asset_id,
                                    a.odometer,
                                    a.odometer_current,
                                    abs((a.odometer_current - ((a.count_multiply)::double precision * a.odometer))) AS multiple_odo,
                                    a.count_multiply,
                                    a.odometer_remain,
                                    a.odometer_threshold
                                   FROM ( SELECT a_1.fleet_id,
                                            a_1.asset_id,
                                            a_1.odometer,
                                            b_1.odometer_current,
                                            count_multiply_odometer((a_1.odometer)::integer, (b_1.odometer_current)::integer) AS count_multiply,
                                            ((count_multiply_odometer((a_1.odometer)::integer, (b_1.odometer_current)::integer) * (a_1.odometer)::integer) % (b_1.odometer_current)::integer) AS odometer_remain,
                                            (a_1.odometer * (0.01)::double precision) AS odometer_threshold
                                           FROM (( SELECT m.id,
                                                    a_1_1.fleet_id,
                                                    m.odometer,
                                                    m.asset_id
                                                   FROM (estate_master_workshop_shedule_plan m
                                                     JOIN asset_asset a_1_1 ON ((m.asset_id = a_1_1.id)))
                                                  WHERE ((m.type)::text <> 'view'::text)) a_1
                                             LEFT JOIN ( SELECT fleet_vehicle_odometer.vehicle_id,
                                                    max(fleet_vehicle_odometer.value) AS odometer_current
                                                   FROM fleet_vehicle_odometer
                                                  GROUP BY fleet_vehicle_odometer.vehicle_id) b_1 ON ((a_1.fleet_id = b_1.vehicle_id)))) a
                                  WHERE ((a.odometer_remain)::double precision <= a.odometer_threshold)) b) mul_odo
                  WHERE (mul_odo.idx = 1);
                   """)

        cr.execute("""CREATE OR REPLACE FUNCTION public.create_mo_preventive()
                     RETURNS boolean
                     LANGUAGE plpgsql
                    AS $function$
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
							    odometer_threshold,
							    (fleet_id ||'-'|| odometer ||'-'||count_multiply) origin
							from vehicle_preventive_odometer
							except
							select vpo.* from
							(
								select origin from mro_order order by id desc
							)mro_order
							inner join
							(
								select
									fleet_id,
								    asset_id,
								    odometer,
								    odometer_current,
								    count_multiply,
								    odometer_remain,
								    odometer_threshold,
								    (fleet_id ||'-'|| odometer ||'-'||count_multiply) origin
								from vehicle_preventive_odometer
							)vpo
							on vpo.origin = mro_order.origin
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
                                    v_vpo.fleet_id ||'-'|| v_vpo.odometer||'-'|| v_vpo.count_multiply,
                                    now(),
                                    1,
                                    v_vpo.asset_id,
                                    1,
                                    1,
                                    'draft',
                                    'pm',
                                    v_vpo.odometer||' km PM for '|| v_vpo.odometer_current ||' km',
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
                    $function$
                   """)
