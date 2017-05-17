# -*- coding: utf-8 -*-
{
    'name': "Employee (Indonesia)",

    'summary': """
        Status, Supervisor Level, Tax, Insurance.""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Cayadi Sutanto <cayadi.sutanto@palmagroup.co.id>, Probo Sukmohadi <probo.sukmohadi@palmagroup.co.id>",
    'website': "http://www.palmagroup.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_attendance', 'hr_contract', 'base_indonesia'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'templates.xml',
        'data/hr_data.xml',
        'views/hr_indonesia_view.xml',
        'views/supervisorlevel_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
        'data/hr_estate_demo.xml',
        'data/hr_employee_demo.xml',
    ],
}