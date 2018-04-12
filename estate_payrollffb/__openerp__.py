# -*- coding: utf-8 -*-
{
    'name': "Estate Payroll FFB (Fresh Fruit Bunches)",

    'summary': """
        Harvesting Labour Payroll Calculation""",

    'description': """
        As human resource and agronomy, they want to administer productivity of harvesting labour so that they can control the harvesting process and calculate exact payroll based on labour's productivity.
    """,

    'author': "Cayadi Sutanto <cayadi.sutanto@palmagroup.co.id>, Probo Sukmohadi <probo.sukmohadi@palmagroup.co.id>, Ardian Pramana <ardian.pramana@palmagroup.co.id",
    'website': "http://www.palmagroup.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Agriculture',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['estate_payroll', 'estate_ffb'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/estate_ffbpayroll_view.xml',
    ],
    # only loaded in demonstration mode (prerequisite data should be processed first)
    'demo': [
        'demo/estate_ffbpayroll_demo.xml',
        
    ],
}