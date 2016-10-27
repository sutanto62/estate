# -*- coding: utf-8 -*-
{
    'name': "Purchase Indonesia",

    'summary': """
       """,

    'description': """
        Module For Purchase , Procurement , And Inventory Indonesia
    """,

    'author': "Mahroza And Probo",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase_request','purchase_requisition','estate','account_budget'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'wizard/reject.xml',
        'views/inherit_purchase_request.xml',
        'views/procur_request_sequence.xml',
        'views/procur_request_view.xml',
        'views/management_good_request.xml',
        'workflow/workflow_procur_good_request.xml'
        # 'templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
