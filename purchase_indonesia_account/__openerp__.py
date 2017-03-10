# -*- coding: utf-8 -*-
{
    'name': "Purchase Indonesia Account Invoice",

    'summary': """
        Inheritance of Account.invoice for purchase_indonesia""",

    'description': """
        This module created to provide purchase indonesia use account.invoice
    """,

    'author': "Mahroza",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'purchases',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase_indonesia'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'templates.xml',
        'views/inherit_stock_picking.xml',
        'views/inherit_account_invoice.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo.xml',
    ],
}