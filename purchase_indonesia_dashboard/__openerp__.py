# -*- coding: utf-8 -*-
{
    'name': "Purchase Indonesia Dashboard Purchase Request",

    'summary': """
       This modul Show dashboard for purchase request""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Mahroza",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase_indonesia','purchase_indonesia_account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/view_inherit_purchase_request_line.xml',
        'views/view_purchase_indonesia_dashboard_pp.xml',
        'views/view_purchase_indonesia_dashboard_tender.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo.xml',
    ],
}