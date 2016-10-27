# -*- coding: utf-8 -*-
{
    'name': "Estate Procurment",

    'summary': """
       """,

    'description': """
        Module For Procurment Estate
    """,

    'author': "Mahroza And Probo",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase_request','purchase_requisition'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/inherit_purchase_request.xml'
        # 'templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}