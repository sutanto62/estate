# -*- coding: utf-8 -*-
{
    'name': "Fingerprint Report",

    'summary': """
        Fingerprint report, calendar, reward point.""",

    'description': """
        Display fingerprint report.
        
        Report Options:
        1. Periodic (Monthly/Weekly).
        2. Company.
        3. Department.
        4. Site Location.
    """,

    'author': "Cayadi Sutanto <cayadi.sutanto@palmagroup.co.id>",
    'website': "http://www.palmagroup.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_fingerprint_ams'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/inherited_hr_fingerprint.xml',
        'wizard/wizard_fingerprint_views.xml',
        'data/print_fingerprint_report_data.xml',
        'report/fingerprint_report_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}