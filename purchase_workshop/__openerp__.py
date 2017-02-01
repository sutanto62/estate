# -*- coding: utf-8 -*-
{
    'name': "Purchase Workshop",

    'summary': """
        Module Purchase Indonesia Can be use on Wokrhop Module""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Mahroza Pradana <Mahroza.pradana@palmagroup.co.id>",
    'website': "http://www.palmagroup.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'estate_production',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase_indonesia','estate_workshop'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/inherit_mro_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}