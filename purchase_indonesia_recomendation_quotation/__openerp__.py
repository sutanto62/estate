# -*- coding: utf-8 -*-
{
    'name': "Purchase Indonesia Recomendation Quotation",

    'summary': """
        this modul to give best price recomendation for user purchase""",

    'description': """

    """,

    'author': "Mahroza Pradana",
    'website': "mahroza.pradana@palmagroup.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase_indonesia'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'templates.xml',
        'views/inherit_purchase_order_line.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo.xml',
    ],
}