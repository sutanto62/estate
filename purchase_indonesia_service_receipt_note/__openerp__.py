# -*- coding: utf-8 -*-
{
    'name': "Purchase Indonesia Service Receipt Note",

    'summary': """
       Module For Service Receipt Note""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Mahroza Pradana <mahroza.pradana@palmagroup.co.id>",
    'website': "http://www.palmagroup.co.id",

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
        'views/inherit_purchase_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}