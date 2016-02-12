# -*- coding: utf-8 -*-
{
    'name': "Estate",

    'summary': """
        Manage Oil Palm Plantation.""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Your Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'templates.xml',
        'views/estate.xml',
        'res_config_view.xml',
        'security/security.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'data/demo.xml',
        'data/stock.location.csv',
        'data/estate.block.template.csv',
        'data/estate.parameter.csv',
        'data/estate.parameter.value.csv'
    ],
}