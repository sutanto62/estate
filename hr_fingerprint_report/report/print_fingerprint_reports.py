from openerp import api, models
import operator

class FingerprintReport(models.AbstractModel):
    _name = 'report.hr_fingerprint_report.report_fingerprint'

    def get_domain(self, data=None):
        """ refactor domain"""
        domain = []
        if data['form']['date_start']:
            domain.append(('date', '>=', str(data['form']['date_start'])))

        if data['form']['date_end']:
            domain.append(('date', '<=', str(data['form']['date_end'])))

        if data['form']['company_id']:
            domain.append(('company_id','=', data['form']['company_id'][0]))

        if data['form']['department_id']:
            domain.append(('department_id','=', data['form']['department_id'][0]))

        if data['form']['contract_type']:
            domain.append(('contract_type', '=', str(data['form']['contract_type'])))

        if data['form']['contract_period']:
            domain.append(('contract_period', '=', str(data['form']['contract_type'])))

        if data['form']['office_level_id']:
            domain.append(('office_level_id', '=', data['form']['office_level_id'][0]))

        return domain

    @api.multi
    def sum_action_reason(self, data=None, reason=None):
        """
        Count number of fingerprint attendance on a reason
        :param reason: action reason
        :type: string
        :return: number of fingerprint attendance by reason
        :rtype: integer
        """
        attendance_obj = self.env['hr_fingerprint_ams.attendance']
        action_reason_ids = attendance_obj.search(self.get_domain(data) + [('action_reason', '=', reason)])
        if reason == 'Cuti':
            res = str(sum(att.p_leave for att in action_reason_ids)) + ' hari'
        elif reason == 'Sakit':
            res = str(sum(att.p_sick for att in action_reason_ids)) + ' hari'
        elif reason == 'Ijin':
            res = str(sum(att.p_permit for att in action_reason_ids)) + ' hari'
        elif reason == 'Dinas Luar':
            res = str(sum(att.p_business_trip for att in action_reason_ids)) + ' hari'
        # Do not sum pulang cepat minute. Attendance with action reason Pulang Cepat did not return early leave.
        # elif reason == 'Pulang Cepat':
        #     res = str(sum(att.p_hour_early_leave for att in action_reason_ids)) + ' menit'

        # elif reason == 'Keluar Kantor':
        #     res = str(sum(att.p_out_office for att in action_reason_ids)) + ' kali'
        else:
            res = ''
        return res

    @api.multi
    def get_attendance_remark(self, data=None):
        """
        Get summary of attendance with action reason.
        Get action reason recordset.
        :param data: form filter
        :type: dictionary
        :return: number of attendance by reason, sorted by name
        :rtype: dict
        """
        list = []
        domain = self.get_domain(data) + [('action_reason', '!=', False)]

        # remark on action reason
        attendance_obj = self.env['hr_fingerprint_ams.attendance']
        action_reason_ids = self.env['hr.action.reason'].search([], order='name asc')
        for reason in action_reason_ids.mapped('name'):
            if reason:
                person = set(attendance_obj.search(domain + [('action_reason', '=', reason)]).mapped('employee_name'))

                print 'reason %s person %s' % (reason, person)
                res = {
                    'reason': str(reason),
                    'person': len(person),
                    'amount': self.sum_action_reason(data, reason)
                }
                list.append(res)

        # other remark - create at XML
        # other_reason = ('p_hour_late_office', 'p_late_amount_office')
        # label = ('Terlambat Kantor (Menit)', 'Terlambat Kantor (X)')
        # for other in other_reason:
        #     domain = self.get_domain(data) + [(other, '>', 0)]
        #     # case
        #     if other == 'p_hour_late_office':
        #         # return amount of person whose attendance > 30
        #
        #         person_amount = 0
        #
        #     res = {
        #         'reason': label[other_reason.index(other)],
        #         # 'person': attendance_obj.search(domain)['employee_name'],
        #         'person': person_amount,
        #         'amount': sum(att.__getitem__(other) for att in attendance_obj.search(domain)),
        #         # 'amount': 0
        #     }
        #     print '  Remark %s: %s, res %s' % (other, domain, res)
        #     list.append(res)
        # print '  Attendance Remark %s' % sorted(list, key=lambda res: res['reason'])
        res = sorted(list, key=lambda res: res['reason'])
        return res

    @api.multi
    def get_department(self, data=None):
        domain = self.get_domain(data)
        attendance_ids = self.env['hr_fingerprint_ams.attendance'].search(domain).mapped('department')
        res = sorted(set(attendance_ids))
        return res

    @api.multi
    def get_attendance(self, data=None):
        """
        Summary of employee attendances. Sorted by Department and Employee
        :param data: form filter.
        :return: sorted
        :rtype: dict
        """
        # count pivot field
        domain_form = self.get_domain(data)
        employee_ids = self.get_employee(data)
        attendance_obj = self.env['hr_fingerprint_ams.attendance']
        dict = []

        # build dict
        for employee in employee_ids:
            # unique employee param: name and nik.
            domain_employee = [('employee_name', '=', employee.name_related),
                               ('nik', '=', employee.nik_number)]

            # exclude 0 day finger if KHL
            if employee.contract_type == '2' and employee.contract_period == '2':
                domain_employee.append(('day_finger', '>', 0))

            domain = domain_form + domain_employee

            attendance_ids = attendance_obj.search(domain)

            # IndexError if no attendance_ids - str(attendance_ids[0].department
            if not attendance_ids:
                continue

            res = {
                'employee_name': employee.name_related,
                'nik': employee.nik_number,

                # get first index - do not loop
                'department': str(attendance_ids[0].department),
                'company': str(attendance_ids[0].company_id.name),

                # loop
                'p_day_normal': sum(att.p_day_normal for att in attendance_ids),
                'p_leave': sum(att.p_leave for att in attendance_ids),
                'p_sick': sum(att.p_sick for att in attendance_ids),
                'p_permit': sum(att.p_permit for att in attendance_ids),
                'p_business_trip': sum(att.p_business_trip for att in attendance_ids),
                'p_out_office': sum(att.p_out_office for att in attendance_ids),
                'p_no_reason': sum(att.p_no_reason for att in attendance_ids),
                'p_day_finger': sum(att.p_day_finger for att in attendance_ids),
                'p_hour_late_office': sum(att.p_hour_late_office for att in attendance_ids),
                'p_late_amount_office': sum(att.p_late_amount_office for att in attendance_ids),
                'p_estate_late': sum(att.p_estate_late for att in attendance_ids),
                'p_estate_late_amount': sum(att.p_estate_late_amount for att in attendance_ids),
                'p_labor_late_circle': sum(att.p_labor_late_circle for att in attendance_ids),
                'p_labor_late_circle_amount': sum(att.p_labor_late_circle_amount for att in attendance_ids),
                'p_labor_late': sum(att.p_labor_late for att in attendance_ids),
                'p_labor_late_amount': sum(att.p_labor_late_amount for att in attendance_ids),
                'p_hour_early_leave': sum(att.p_hour_early_leave for att in attendance_ids),
                'p_early_leave_amount': sum(att.p_early_leave_amount for att in attendance_ids),
                'p_sign_percent': sum(att.p_sign_percent for att in attendance_ids)/len(attendance_ids) if len(attendance_ids) > 0 else 0,
                'p_hour_work_float': sum(att.p_hour_work_float for att in attendance_ids),
                'p_average_day_work': sum(att.p_average_day_work for att in attendance_ids)/len(attendance_ids) if len(attendance_ids) > 0 else 0,
                'p_piece_rate_day': sum(att.p_piece_rate_day for att in attendance_ids),
            }
            dict.append(res)

        return sorted(dict, key=operator.itemgetter('department', 'nik', 'employee_name'))

    @api.multi
    def get_employee(self, data=None):
        """
        Get unique employee by name and nik, sorted by department and employee name
        :param data: form filter
        :return: employee recordset
        :rtype: object
        """
        # nik must unique
        attendance_obj = self.env['hr_fingerprint_ams.attendance']
        attendance_nik_ids = set(attendance_obj.search(self.get_domain(data), order='nik asc').mapped('nik'))
        employee_ids = self.env['hr.employee'].search([('nik_number', 'in', list(attendance_nik_ids))], order='name_related asc')
        return employee_ids

    @api.multi
    def get_color(self, type, late):
        """
        Define font awesome class. Make sure XML has fontawesome CSS class. Make sure param type registered at var a
        :param type: fingerprint attendance field
        :type: string
        :param late: number
        :type: integer
        :return: HTML stylesheet
        :rtype: string
        """
        # potong poin = p_hour_late_office, p_late_amount_office, p_estate_late_amount
        a = [
            'p_hour_late_office', # Terlambat (MNT) Kary Kantor
            'p_late_amount_office', # Terlambat (X) Kary Kantor
            'p_estate_late', # Terlambat Menit Kebun
            'p_estate_late_amount', # Terlambat X Kebun
            'p_labor_late_circle', # Terlambat Menit KHL (Apel)
            'p_labor_late_circle_amount', # Terlambat X KHL Apel
            'p_labor_late', # Terlambat Menit KHL Kerja
            'p_labor_late_amount' # Terlambat X KHL Kerja
        ]

        # non-registered type got white background
        color = 'white'

        # p_hour_late_office
        if type == a[0]:
            if 31 <= late <= 60:
                color = 'gold'
            if 61 <= late <= 90:
                color = 'red'
            if late >= 91:
                color = 'black'

        # p_late_amount_office
        if type == a[1]:
            if 4 <= late <= 6:
                color = 'gold'
            if 7 <= late <= 12:
                color = 'red'
            if late >= 13:
                color = 'black'

        # p_estate_late
        if type == a[2]:
            if late >= 1:
                color = 'goldenrod'

        # p_estate_late_amount
        if type == a[3]:
            if late >= 4:
                color = 'red'

        # p_labor_late_circle
        if type == a[4]:
            if late >= 1:
                color = 'goldenrod'

        # p_labor_late_circle_amount
        if type == a[5]:
            if late >= 1:
                color = 'goldenrod'

        # p_labor_late
        if type == a[6]:
            if late >= 1:
                color = 'goldenrod'

        # p_labor_late_amount
        if type == a[7]:
            if late >= 1:
                color = 'goldenrod'

        res = 'fa fa-circle-%s' % color
        return res

    @api.multi
    def render_html(self, data):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('hr_fingerprint_report.report_fingerprint')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'data': data,
            'remarks': self.get_attendance_remark(data),
            'departments': self.get_department(data),
            'attendances': self.get_attendance(data),
            'get_color': self.get_color,
        }
        return report_obj.render('hr_fingerprint_report.report_fingerprint', docargs)