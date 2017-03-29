# -*- coding: utf-8 -*-
{
    'name': "Purchase Indonesia Inventory Manage",

    'summary': """
        Inventory Manage For module Purchase Indonesia""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Mahroza Pradana",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchases',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase_indonesia'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'wizard/reject.xml',
        'views/view_purchase_indonesia_good_request.xml',
        'views/view_purchase_indonesia_management_good.xml',
        'views/view_purchase_indonesia_good_return.xml',
        'views/purchase_indonesia_sequence.xml',
        'views/view_purchase_indonesia_goods_report_in.xml',
        'views/view_purchase_indonesia_goods_report_out.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}