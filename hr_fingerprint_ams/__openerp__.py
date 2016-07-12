# -*- coding: utf-8 -*-
{
    'name': "Fingerprint Solution",

    'summary': """
        Attendance, Fingerprint, Solution""",

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
    'depends': ['base', 'hr_attendance', 'hr_indonesia'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'templates.xml',
        'views/hr_fingerprint.xml',
        'views/inherited_hr_attendance_view.xml',
        'views/inherited_estate_upkeep_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
        # 'data/hr.attendance.demo.csv',
        # 'data/hr.attendance.demo.csv',
    ],
}