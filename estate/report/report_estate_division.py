#-*- coding:utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv
from openerp.report import report_sxw
from datetime import date
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from decimal import *

import time

STATE = ('approved', 'correction', 'payslip')

class estate_division_report(report_sxw.rml_parse):
    """
    Estate Division Report shows all approved/correction/payslip activities. It shows
    1. Activity.
    2. Location.
    3. Labour work days, overtime and piece rate.
    4. Work result (activity and material usage quantity).
    5. Cost (daily wages, overtime, piece rate, material).
    6. Ratio.

    Record based on labour's activity (constraints by upkeep activity)
    """

    def __init__(self, cr, uid, name, context):
        super(estate_division_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_upkeep': self._get_upkeep,
            'get_upkeep_activity': self._get_upkeep_activity,
            'get_location_name': self._get_location_name,
            'get_block_name': self._get_block_name,
            'get_number_of_days': self._get_number_of_days,
            'get_upkeep_labour_by_location': self._get_upkeep_labour_by_location,
            'get_upkeep_activity_material': self._get_upkeep_activity_material,
            'get_location_length': self._get_location_length,
        })

    def set_context(self, objects, data, ids, report_type=None):
        upkeep_obj = self.pool.get('estate.upkeep')
        ctx = data['form'].get('used_context', {})
        self.date_start = data['form'].get('date_start', time.strftime('%Y-%m-%d'))
        self.date_end = data['form'].get('date_end', time.strftime('%Y-%m-%d'))
        self.estate_id = data['form'].get('estate_id')
        self.division_id = data['form'].get('division_id')

        return super(estate_division_report, self).set_context(objects, data, ids, report_type=report_type)

    def _get_upkeep(self, data):
        """
        Get approved/correction/payslip upkeep based on date, estate and/or division.
        :param data:
        :return: list of estate upkeep instance
        """
        upkeep_obj = self.pool.get('estate.upkeep')
        if self.estate_id and self.division_id:
            ids = upkeep_obj.search(self.cr, self.uid, [('state', 'in', STATE),
                                                        ('date', '>=', self.date_start),
                                                        ('date', '<=', self.date_end),
                                                        ('division_id', '=', self.division_id[0])])
        elif self.estate_id:
            ids = upkeep_obj.search(self.cr, self.uid, [('state', 'in', STATE),
                                                        ('date', '>=', self.date_start),
                                                        ('date', '<=', self.date_end),
                                                        ('estate_id', '=', self.estate_id[0])])
        res = upkeep_obj.browse(self.cr, self.uid, ids)
        return res

    def _get_upkeep_activity(self, data):
        """
        Get sorted active activity of selected upkeep
        :param data: wizard input
        :return: sorted list of activity
        """
        activity_ids = []
        activity_hierarchy = []
        res = []
        res_sorted = []

        # Get normal activity
        for record in self._get_upkeep(data):
            for activities in record.activity_line_ids:
                activity_ids.append(activities.activity_id)
        res += set(activity_ids)

        # Get view activity
        for activity in set(activity_ids):
            parent = False
            if activity.parent_id:
                parent = True
            while parent:
                if activity.parent_id:
                    activity_hierarchy.append(activity.parent_id)
                    activity = activity.parent_id
                else:
                    parent = False
        res += set(activity_hierarchy)

        # Arrange activity
        res_sorted = sorted(res, key=lambda field: field['complete_name'])

        return res_sorted

    def _get_upkeep_labour_by_location(self, activity):
        """
        Get number of day, overtime and piece rate based on upkeep labour. It keep location and real work result.
        Caution: upkeep activity that has no labour return 0 number of day, overtime and piece rate - but still shown.
        :param activity:
        :return:
        """

        # query if estate and division are true. need to fix for estate only.
        group_by = 'location_id'
        query = 'SELECT row_number() over(order by l.location_id) as id, l.location_id as location_id, sum(l.number_of_day) as number_of_day, ' \
                + self._sub_query_ytd('number_of_day', activity, group_by) + ', ' \
                'sum(l.quantity_overtime) as quantity_overtime, ' \
                + self._sub_query_ytd('quantity_overtime', activity, group_by) + ', ' \
                'sum(l.quantity_piece_rate) as quantity_piece_rate, ' \
                + self._sub_query_ytd('quantity_piece_rate', activity, group_by) + ', ' \
                'sum(l.wage_number_of_day) as wage_number_of_day, ' \
                + self._sub_query_ytd('wage_number_of_day', activity, group_by) + ', ' \
                'sum(l.wage_overtime) as wage_overtime, ' \
                + self._sub_query_ytd('wage_overtime', activity, group_by) + ', ' \
                'sum(l.wage_piece_rate) as wage_piece_rate, ' \
                + self._sub_query_ytd('wage_piece_rate', activity, group_by) + ', ' \
                'sum(l.quantity) as quantity, ' \
                + self._sub_query_ytd('quantity', activity, group_by) + ' ' \
                'FROM estate_upkeep_labour l ' \
                'WHERE l.activity_id = %s AND ' \
                'l.estate_id = %s AND ' \
                'l.division_id = %s AND ' \
                'l.state in %s AND ' \
                'l.upkeep_date >= \'%s\' AND ' \
                'l.upkeep_date <= \'%s\' ' \
                'group by l.%s;' % (activity.id, self.estate_id[0], self.division_id[0], STATE,
                                    self.date_start, self.date_end, group_by)
        self.cr.execute(query)
        res = self.cr.dictfetchall()
        return res

    def _get_location_length(self, activity):
        """Required to format activity which has multi location
        """
        res = len(self._get_upkeep_labour_by_location(activity))
        return res

    def _sub_query_ytd(self, col, activity, group_by):
        """
        Get year to date
        :param col: column name
        :param activity: activity
        :param group_by: use 'location_id' for ytd per location and 'activity_id' for ytd per activity
        :return: sum of column
        """
        # Make sure start from Jan 1.
        start = datetime.strptime(self.date_start, DF).replace(month=1, day=1).strftime(DF)
        query = '(SELECT sum(%s) ' \
                'FROM estate_upkeep_labour ' \
                'WHERE activity_id = %s AND ' \
                'estate_id = %s AND ' \
                'division_id = %s AND ' \
                'state in %s AND ' \
                'upkeep_date >= \'%s\' AND ' \
                'upkeep_date <= \'%s\' AND ' \
                '%s = l.%s ' \
                'group by %s) as ytd_%s' % (col, activity.id, self.estate_id[0], self.division_id[0],
                                            STATE, start, self.date_end, group_by, group_by, group_by, col)
        return query

    def _get_upkeep_activity_material(self, activity, qty_location):
        """
        Get activity's material usage by location. Note: material usage will be proportionally split based on activity quantity
        :param activity: activity
        :param qty_location: location where activity happened
        :return: amount of material for selected activity and location

        Ex.
        n1, n2, n... are quantity of upkeep labour activity's quantity
        Activity A with Material A n1 kg - Location A (y1:10%), B (y2:230%), C (y3:60%).
        Activity B with Material A n2 kg - Location A (y4:75%), D (y5:25%).

        LHA
        Activity A, Location A, Qty sum(y1+y4), Material (y1*n1)+(y4*n2)
        Activity A, Location B, Qty sum(y2), Material (y2*n1)
        Activity A, Location C, Qty sum(y3), Material (y3*n1)
        Activity D, Location D, qty sum(y5), Material (y5*n2)
        """
        # get total quantity of activity from upkeep labour (not upkeep activity)
        group_by = 'activity_id'
        query_quantity = 'SELECT l.activity_id, ' \
                'sum(l.quantity) as quantity, ' \
                + self._sub_query_ytd('quantity', activity, group_by) + ' ' \
                'FROM estate_upkeep_labour l ' \
                'WHERE l.activity_id = %s AND ' \
                'l.estate_id = %s AND ' \
                'l.division_id = %s AND ' \
                'l.state in %s AND ' \
                'l.upkeep_date >= \'%s\' AND ' \
                'l.upkeep_date <= \'%s\' ' \
                'group by l.%s;' % (activity.id, self.estate_id[0], self.division_id[0], STATE,
                                    self.date_start, self.date_end, group_by)

        self.cr.execute(query_quantity)
        res_quantity = self.cr.dictfetchall()

        # compute material usage per location
        if res_quantity:
            # default precision 6
            ratio = qty_location/res_quantity[0]['quantity']
            # ratio should use 2 decimal precision
            query_materials = 'SELECT row_number() over(order by m.activity_id) as id, ' \
                              'm.activity_id as activity_id, pt.name as name, ' \
                              'u.name as uom, sum(m.unit_amount)*%.6f as unit_amount, ' \
                              'sum(m.unit_amount)*%.6f*m.product_standard_price as amount ' \
                              'FROM estate_upkeep_material m ' \
                              'LEFT JOIN product_product p on (p.id = m.product_id) ' \
                              'LEFT JOIN product_template pt on (pt.id = p.product_tmpl_id) ' \
                              'LEFT JOIN product_uom u on (u.id = pt.uom_id) ' \
                              'WHERE ' \
                              'm.activity_id = %s AND m.estate_id = %s AND m.division_id = %s AND ' \
                              'm.state in %s AND m.upkeep_date >= \'%s\' AND ' \
                              'm.upkeep_date <= \'%s\' group by m.activity_id, pt.name, ' \
                              'u.name, m.product_standard_price;' % \
                              (ratio, ratio, activity.id, self.estate_id[0], self.division_id[0], STATE,
                               self.date_start, self.date_end)
            self.cr.execute(query_materials)
            res_materials = self.cr.dictfetchall()
            return res_materials

    def _get_location_name(self, list):
        """
        Get name
        :param id: location id
        :return: location name (not complete_name)
        """
        location_obj = self.pool.get('stock.location')
        # search return ids, browse return instances
        ids = location_obj.search(self.cr, self.uid, [('id', '=', list[0])])
        res = location_obj.browse(self.cr, self.uid, ids)
        return res.name

    def _get_block_name(self, id):
        location_obj = self.pool.get('estate.block.template')
        # search return ids, browse return instances
        ids = location_obj.search(self.cr, self.uid, [('id', '=', id)])
        res = location_obj.browse(self.cr, self.uid, ids)
        return res.name

    def _get_number_of_days(self, data, id, ytd=False):
        """
        DEPRECATED - swtich to _get_upkeep_labour_by_location
        Get number of days for certain activity
        :param data: wizard input
        :param id: activity id
        :param ytd: year to date flag
        :return: int: number of days
        """
        upkeep_obj = self.pool.get('estate.upkeep.labour')

        if self.estate_id and self.division_id:
            ids = upkeep_obj.search(self.cr, self.uid, [('activity_id', '=', id),
                                                        ('estate_id', '=', self.estate_id[0]),
                                                        ('division_id', '=', self.division_id[0]),
                                                        ('state', 'in', STATE),
                                                        ('upkeep_date', '>=', self.date_start),
                                                        ('upkeep_date', '<=', self.date_end)])
        else:
            ids = upkeep_obj.search(self.cr, self.uid, [('activity_id', '=', id),
                                                        ('estate_id', '=', self.estate_id[0]),
                                                        ('state', 'in', STATE),
                                                        ('upkeep_date', '>=', self.date_start),
                                                        ('upkeep_date', '<=', self.date_end)])

        labour_ids = upkeep_obj.browse(self.cr, self.uid, ids)
        if ytd:
            res = 100
        else:
            res = sum([labour.number_of_day for labour in labour_ids])
        return res

class wrapped_report_estate_division(osv.AbstractModel):
    _name = 'report.estate.report_estate_division'
    _inherit = 'report.abstract_report'
    _template = 'estate.report_estate_division'
    _wrapped_report_class = estate_division_report

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: