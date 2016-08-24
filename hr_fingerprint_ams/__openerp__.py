# -*- coding: utf-8 -*-
{
    'name': "Fingerprint Solution",

    'summary': """
        Attendance, Fingerprint, Payroll""",

    'description': """
        Extend attendance to use export data from AMS solution.co.id
    """,

    'author': "Your Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    # please include estate_payroll to override get_worked_days
    'depends': ['base', 'hr_attendance', 'hr_indonesia', 'estate_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'templates.xml',
        'views/hr_fingerprint.xml',
        'views/inherited_hr_attendance_view.xml',
        'views/inherited_estate_upkeep_view.xml',
        'security/menu_items.xml',  # call this xml after all views xml setup
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
        'data/attendance_demo.xml',
    ],
}