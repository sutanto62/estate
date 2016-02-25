# -*- coding: utf-8 -*-
{
    'name': "Estate Vehicle",

    'summary': """
        Estate Management Additional for Vehicle""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Mahroza",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','fleet','hr'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml','views/estate_nursery_vehicle.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}