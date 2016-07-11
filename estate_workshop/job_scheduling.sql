-- View: public.vehicle_preventive_odometer

-- DROP VIEW public.vehicle_preventive_odometer;

CREATE OR REPLACE VIEW vehicle_preventive_odometer AS
 SELECT a.fleet_id,
    a.asset_id,
    a.odometer,
    b.odometer_current,
    count_multiply_odometer(a.odometer::integer, b.odometer_current::integer) AS count_multiply,
    count_multiply_odometer(a.odometer::integer, b.odometer_current::integer) * a.odometer::integer % b.odometer_current::integer AS odometer_remain,
    a.odometer * 0.01::double precision AS odometer_threshold
   FROM ( SELECT m.id,
            a_1.fleet_id,
            m.odometer,
            m.asset_id
           FROM estate_master_workshop_shedule_plan m
             JOIN asset_asset a_1 ON m.asset_id = a_1.id
          WHERE m.type::text <> 'view'::text) a
     LEFT JOIN ( SELECT fleet_vehicle_odometer.vehicle_id,
            max(fleet_vehicle_odometer.value) AS odometer_current
           FROM fleet_vehicle_odometer
          GROUP BY fleet_vehicle_odometer.vehicle_id) b ON a.fleet_id = b.vehicle_id;

ALTER TABLE vehicle_preventive_odometer
  OWNER TO odoo;


  -- Function: public.count_multiply_odometer(integer, integer)

-- DROP FUNCTION public.count_multiply_odometer(integer, integer);

CREATE OR REPLACE FUNCTION count_multiply_odometer(i_odometer integer, i_odometer_current integer)
  RETURNS integer AS
\$BODY\$
declare
	count_multiply integer;
begin
	count_multiply = 1;

	while (count_multiply * i_odometer < i_odometer_current) loop
		count_multiply = count_multiply + 1;
	end loop;

	return count_multiply;
end;
\$BODY\$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION count_multiply_odometer(integer, integer)
  OWNER TO odoo;


-- Function: public.create_mo_preventive()

-- DROP FUNCTION public.create_mo_preventive();

CREATE OR REPLACE FUNCTION create_mo_preventive()
  RETURNS boolean AS
\$BODY\$
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
\$BODY\$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION create_mo_preventive()
  OWNER TO odoo;