# -*- coding: utf-8 -*-
{
    'name': "Employee (Indonesia)",

    'summary': """
        Employee Status, Tax, Insurance.""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Your Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_attendance', 'hr_contract'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/hr_indonesia_view.xml',
        'data/hr_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
        'data/hr.employee.csv',
        'data/res.users.csv',
        'data/hr_estate_demo.xml',
    ],
}