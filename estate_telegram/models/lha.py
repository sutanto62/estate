# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime
from dateutil import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class Lha(models.TransientModel):
    """
    Create content for Telegram response
    """

    _name = 'estate_telegram.lha'
    _description = 'Estatae Telegram LHA'


    @api.model
    def test(self):
        # User login to odoo via palmabot
        # Get his division
        # Sum quantity, number of day, overtime, piece rate, ratio of activities
        return True

    @api.model
    def report(self,day=1):
        report = {}
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)],
                                                     limit=1, order='name asc')
        estate_id = employee_id.estate_id

        # H-1 report
        lha_date = (datetime.today() + relativedelta.relativedelta(days=-day)).strftime(DF)

        data = {
            'form': {
                'date_start': lha_date,
                'date_end': lha_date,
                'estate_id': estate_id.inherit_location_id.ids,
            }
        }

        report['upkeep_date'] = data['form']['date_start']
        report['assistant'] = employee_id.name

        division_ids = []
        asst_divisions = self.division()
        for division in asst_divisions:
            # set domain
            data['form']['division_id'] = division.inherit_location_id.ids
            activity_ids = self.activities(data)

            # do not display division without activity
            if activity_ids:
                val = {
                    'division': division.name,
                    'activities': activity_ids
                }
                division_ids.append(val)
        report['division_ids'] = division_ids
        return report

    @api.model
    def division(self):
        """
        Division under current user supervision
        :return: recordsets of division
        :rtype: recordsets
        """
        division_ids = []
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)],
                                                     limit=1, order='name asc')
        if employee_id:
            division_ids = self.env['estate.block.template'].search([('estate_location_level', '=', '2'),
                                                                     ('assistant_id', '=', employee_id.id)],
                                                                    order='name asc')
        return division_ids

    @api.model
    def activities(self, data):
        """
        Wrapper of report_estate_division
        :param vals: parameter
        :return:
        """
        report_obj = self.env['report.estate.report_estate_division']
        res = report_obj.get_activity(data)
        return res
