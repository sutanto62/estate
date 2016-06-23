
/* generate holiday peryear */

CREATE OR REPLACE FUNCTION insert_range_into_calendar(from_date date, to_date date)
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