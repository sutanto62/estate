# -*- coding: utf-8 -*-
{
    'name': "Estate Account",

    'summary': """
        Payroll, Estate, Account Move""",

    'description': """
        Create Account Move based on Payroll and Estate Upkeep
    """,

    'author': "Cayadi Sutanto <cayadi.sutanto@palmagroup.co.id>",
    'website': "http://www.palmagroup.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Agriculture',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'estate', 'estate_payroll', 'account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'templates.xml',
        'data/account_data.xml',
        'data/labour_account.xml',
        'views/inherited_estate_activity_view.xml',
        'views/inherited_estate_upkeep.xml',
        'views/inherited_hr_payroll_view.xml',
        'views/inherited_account_view.xml',
        'views/estate_account_view.xml' # error menu and action did not appear,
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}