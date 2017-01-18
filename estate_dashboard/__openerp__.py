# -*- coding: utf-8 -*-
{
    'name': "Estate Dashboard",

    'summary': """
        Upkeep, Labour, Material""",

    'description': """
        Display progress of entry
    """,

    'author': "Cayadi Sutanto, Probo Sukmohadi",
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
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/estate_views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}