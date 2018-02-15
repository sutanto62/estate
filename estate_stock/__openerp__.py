# -*- coding: utf-8 -*-
{
    'name': "Estate Stock",

    'summary': """
        Estate Stock Move, Unit Conversion, Telegram notification""",

    'description': """
        Description
    """,

    'author': "Cayadi Sutanto <cayadi.sutanto@palmagroup.co.id>",
    'website': "http://www.palmagroup.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Agriculture',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','estate'],

    # always loaded
    'data': [
        'security/estate_stock_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'data/stock_warehouse.xml',
        'data/res_groups.xml',
        'data/record_rule_data.xml',
        'views/material_order_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
        'demo/material_order_demo.xml',
        'demo/res_user_demo.xml',
    ],
}