# -*- coding: utf-8 -*-
{
    'name': "Estate GIS",

    'summary': """
        GIS Block""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Cayadi Sutanto <cayadi.sutanto@palmagroup.co.id>, Probo Sukmohadi <probo.sukmohadi@palmagroup.co.id>",
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
        'templates.xml',
        'views/inherited_estate.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}