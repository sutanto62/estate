from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
from pytz import timezone
import calendar
import decimal


class CountMultiplyOdometer(models.Model):

    _name = "count.multiply.odometer"
    _description = "Function to Jobs Sheduling"
    _auto = False

    def init(self, cr):
        cr.execute("""CREATE OR REPLACE FUNCTION count_multiply_odometer(i_odometer integer, i_odometer_current integer)
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
                   """)

class CountMultiplyOdometer(models.Model):

    _name = "create.mo.preventive"
    _description = "Function to Jobs Sheduling"
    _auto = False

    def init(self, cr):
        cr.execute("""CREATE OR REPLACE FUNCTION create_mo_preventive()
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
                  COST 100;""")