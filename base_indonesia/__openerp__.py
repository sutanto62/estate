# -*- coding: utf-8 -*-
{
    'name': "Base Indonesia",

    'summary': """
        The modules Inherit Base in Odoo Module""",

    'description': """
        Module inherit base module on Odoo Addons
    """,

    'author': "Mahroza And Probo",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'base',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'templates.xml',
        'views/inherit_res_company.xml',
        'views/inherit_res_partner.xml',
        'views/sequence_res_partner.xml',
        'views/inherit_res_country_state.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'data/res.company.csv',
    ],
}