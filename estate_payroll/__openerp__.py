# -*- coding: utf-8 -*-
{
    'name': "Estate Payroll",

    'summary': """
        Estate Worker Payslip, Estate & Division wise.""",

    'description': """
Upkeep Labour Integration
=========================

This module extend existing HR Payroll. Using its Payslip Batches to collect upkeep labour
wage, overtime and piece rate. It has Upkeep button which selects all employee which has
approved upkeep labour at defined Payslip Batches period. Use Payroll Type (employee,
estate or division) to filter.

Salary Structure
----------------

There are three salary components.

* Basic Wage, with code WORK300 will be used to calculate daily wage.
* Overtime, with code OT is flat overtime amount.
* Piece Rate, with code PR is sum of upkeep labour's piece rate amount.

    """,

    'author': "Cayadi Sutanto <cayadi.sutanto@palmagroup.co.id>, Probo Sukmohadi <probo.sukmohadi@palmagroup.co.id>",
    'website': "http://www.palmagroup.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_payroll'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/menu_items.xml',
        'security/record_rules.xml',
        'security/record_rules.xml',
        'views/inherited_hr_payroll_view.xml',
        'views/inherited_estate_hr_view.xml',
        'views/report_estate_payslip.xml',
        'views/report_bpjs.xml',
        'estate_payroll_report.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'data/hr_payroll_structure_demo.xml',
        'data/resource_calendar_data.xml',
        'data/hr_contract_demo.xml',
        'data/payroll_run_demo.xml',
    ],
}