# -*- coding: utf-8 -*-
{
    'name': "Rainfall",

    'summary': """
        Rainfall, Observation Settings""",

    'description': """
        Create rainfall record using observation configuration. Rainfall were recorded
        twice a day, morning and evening. Configuration define start time, end time and method.
    """,

    'author': "Cayadi Sutanto <cayadi.sutanto@palmagroup.co.id>",
    'website': "http://www.palmagroup.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Agriculture',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'estate'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'res_config_view.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/rainfall.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}