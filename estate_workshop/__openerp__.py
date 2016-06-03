# -*- coding: utf-8 -*-
{
    'name': "Estate Workshop",

    'summary': """
        Modul Workshop for Estate""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Mahroza And Probo",
    'website': "http://www.palmagroup.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','asset','mro','estate_vehicle'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/estate_asset.xml',
        'views/estate_notification.xml',
        'views/estate_master_catalog.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}