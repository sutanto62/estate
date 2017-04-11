#-*- coding:utf-8 -*-

from openerp import api, models, _


class ParticularReport(models.AbstractModel):
    _name = 'report.estate_payroll.report_bpjs'

    @api.multi
    def get_payslip_bpjs(self, payslip_ids):
        bpjs_rule_ids = self.env['hr.salary.rule'].search([('bpjs', '=', True)])
        salary_structure_ids = self.env['hr.payroll.structure'].search([('rule_ids.id', 'in', bpjs_rule_ids.ids)])
        res = payslip_ids.search([('struct_id', 'in', salary_structure_ids.ids)])
        return res

    @api.multi
    def sum_wage(self, payslip):
        line_obj = self.env['hr.payslip.line']
        line_ids = line_obj.search([('id', 'in', payslip.line_ids.ids),
                               ('code', '=', ('EDW', 'OT', 'PR'))])
        res = sum(line.total for line in line_ids)
        return res

    @api.multi
    def get_jkkc(self, payslip_line_ids):
        line_obj = self.env['hr.payslip.line']
        res = line_obj.search([('id', 'in', payslip_line_ids.ids),
                               ('code', '=', 'JKKC')])
        return res.total

    @api.multi
    def get_jkmc(self, payslip_line_ids):
        line_obj = self.env['hr.payslip.line']
        res = line_obj.search([('id', 'in', payslip_line_ids.ids),
                               ('code', '=', 'JKMC')])
        return res.total


    @api.multi
    def render_html(self, data):
        report_obj = self.env['report']
        payslip_obj = self.env['hr.payslip']
        report = report_obj._get_report_from_name('estate_payroll.report_bpjs')
        docs = self.env[report.model].browse(self._ids)

        # Limit payslip at selected payslip run
        payslip_ids = payslip_obj.search([('payslip_run_id', 'in', docs.ids)], order="name asc")

        # Display gender and marital text
        gender = {"male": _("Male"), "female": _("Female"), "other": _("Other Gender")}
        marital = {"single": _("Single"), "married": _("Married"), "widower": _("Widower"), "divorced": _("Divorced")}

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': docs,
            'Payslip': self.get_payslip_bpjs(payslip_ids),
            'sum_wage': self.sum_wage,
            'get_jkkc': self.get_jkkc,
            'get_jkmc': self.get_jkmc,
            'gender': gender,
            'marital': marital,
        }
        return report_obj.render('estate_payroll.report_bpjs', docargs)