# -*- coding: utf-8 -*-
{
    'name': "Estate FFB (Fresh Fruit Bunches)",

    'summary': """
        Harvesting Administration""",

    'description': """
        As agronomy, they want to administer result of ffb so that they can get quantity and control quality of its ffb and harvesting process.
    """,

    'author': "Cayadi Sutanto <cayadi.sutanto@palmagroup.co.id>, Probo Sukmohadi <probo.sukmohadi@palmagroup.co.id>, Ardian Pramana <ardian.pramana@palmagroup.co.id",
    'website': "http://www.palmagroup.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Agriculture',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['estate'],

    # always loaded
    'data': [
        'data/ir_sequence_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/inherit_estate_hr_team_views.xml',
        'views/estate_ffb_standard_view.xml',
        'views/estate_ffb_view.xml',
        'views/estate_ffb_detail_views.xml',
    ],
    # only loaded in demonstration mode (prerequisite data should be processed first)
    'demo': [
        'demo/res_user_demo.xml',
        'demo/ffb_demo.xml',
    ],
}