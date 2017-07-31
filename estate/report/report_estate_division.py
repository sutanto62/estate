from openerp import api, models

class ParticularReport(models.AbstractModel):
    _name = 'report.estate.report_estate_division'

    @api.multi
    def get_planted_year(self, data):
        """ avoid looping at xml"""

        # todo company_id belum
        query = 'select distinct '\
                '    case '\
                '        when b.name isnull then \'LC\' '\
                '        when left(lower(b.name), 5) = \'batch\' then \'Pembibitan\' '\
                '        else b.name '\
                '    end "name" '\
                'from estate_upkeep_labour a '\
                'left join estate_planted_year b on b.id = a.planted_year_id ' \
                'where ' \
                '    a.upkeep_date between \'%s\' and \'%s\' ' \
                '    and a.estate_id = %s ' \
                '    and a.division_id = %s ' \
                'order by '\
                '    1 desc;' % (str(data['form']['date_start']),
                                 str(data['form']['date_end']),
                                 data['form']['estate_id'][0],
                                 data['form']['division_id'][0])
        self._cr.execute(query)
        res = self._cr.dictfetchall()
        return res

    @api.multi
    def get_activity(self, data):
        """ group by activity at any state (draft, approved, payslip, etc.)"""
        query = 'select '\
                '   case '\
                '        when b.name isnull then \'LC\' '\
                '        when left(lower(b.name), 5) = \'batch\' then \'Pembibitan\' '\
                '        else b.name '\
                '    end "year", '\
                '    e.code "coa", '\
                '    c.name "activity", '\
                '    d.name "uom", '\
                '    coalesce(sum(a.quantity), 0) "quantity", '\
                '    coalesce(sum(a.number_of_day), 0) "number_of_day", '\
                '    coalesce(sum(a.quantity_overtime), 0) "overtime", '\
                '    coalesce(sum(a.quantity_piece_rate), 0) "piece_rate", '\
                '    sum(a.amount) "total", '\
                '    case '\
                '        when (sum(a.quantity) > 0) and (sum(a.number_of_day) > 0) '\
                '            then (sum(a.quantity)/sum(a.number_of_day))::numeric(10,2) '\
                '        else 0 ' \
                '    end "qty_per_day", '\
                '    case '\
                '        when (sum(a.quantity) > 0) and (sum(a.number_of_day) > 0) '\
                '            then (sum(a.number_of_day)/sum(a.quantity))::numeric(10,6) '\
                '        else 0 '\
                '    end "day_per_qty", ' \
                '    case '\
                '        when(sum(a.amount) > 0) and (sum(a.quantity) > 0) '\
                '        then(sum(a.amount) / sum(a.quantity))::numeric(14, 2) '\
                '        else 0 '\
                '    end "total_per_qty" '\
                'from estate_upkeep_labour a '\
                'left join estate_planted_year b on b.id = a.planted_year_id '\
                'left join estate_activity c on c.id = a.activity_id '\
                'left join product_uom d on d.id = c.uom_id '\
                'left join account_account e on e.id = c.general_account_id ' \
                'where ' \
                '    a.upkeep_date between \'%s\' and \'%s\'' \
                '    and a.estate_id = %s' \
                '    and a.division_id = %s' \
                'group by '\
                '    1,2,3,4 '\
                'order by '\
                '    1 desc, 2 '\
                '    ;' % (str(data['form']['date_start']),
                           str(data['form']['date_end']),
                           data['form']['estate_id'][0],
                           data['form']['division_id'][0])

        self._cr.execute(query)
        res = self._cr.dictfetchall()
        return res

    @api.multi
    def get_upkeep_activity(self, data, year=None):
        """ get planted year from upkeep labour"""
        upkeep_labour_obj = self.env['estate.upkeep.labour']

        domain = [('upkeep_date', '>=', str(data['form']['date_start'])),
                  ('upkeep_date', '<=', str(data['form']['date_end']))]

        if data['form']['estate_id']:
            domain.append(('estate_id', '=', data['form']['estate_id'][0]))

        if data['form']['division_id']:
            domain.append(('division_id', '=', data['form']['division_id'][0]))

        if data['form']['company_id']:
            domain.append(('company_id', '=', data['form']['company_id'][0]))

        # return False if no recordset
        res = upkeep_labour_obj.search(domain)

        return res

    @api.multi
    def render_html(self, data):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('estate.report_estate_division')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'years': self.get_planted_year(data),
            'upkeeps': self.get_upkeep_activity(data),
            'activities': self.get_activity(data),
            'data': data
        }
        return report_obj.render('estate.report_estate_division', docargs)
