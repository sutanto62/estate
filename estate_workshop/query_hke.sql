CREATE OR REPLACE FUNCTION somefuncname(i_bulan int,i_tahun int,i_vehicle_id int, i_status int) RETURNS int LANGUAGE plpgsql AS $BODY$
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