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
    'depends': ['base', 'stock', 'hr_indonesia', 'account', 'base_geoengine','mail'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'templates.xml',
        'views/estate.xml',
        'views/estate_activity_view.xml',
        'views/estate_hr_view.xml',
        'views/estate_upkeep.xml',
        'views/inherited_product_category_view.xml',
        'res_config_view.xml',
        'data/estate_uom_data.xml',
        'data/hr_data.xml',
        'views/report_estate_division.xml',
        'estate_report.xml',
    ],
    # only loaded in demonstration mode (prerequisite data should be processed first)
    'demo': [
        'data/demo.xml',
        'data/account_analytic.xml',
        'data/stock.location.csv',
        'data/estate.block.template.csv',
        #'data/estate.hr.team.csv',
        'data/estate.parameter.csv',
        'data/estate.parameter.value.csv',
        'data/estate.stand.hectare.csv',
        'data/product.template.csv',
        #'data/res.users.csv',
        #'data/hr_demo.xml',
        #'data/demo.xml',
        'data/hr_contract_demo.xml',
        'data/estate_hr_team_demo.xml',
        'data/inherited_product_demo.xml',
        'data/estate.activity.csv',
        'data/activity_material.xml',
        'data/upkeep_demo.xml',
        #'data/hr.employee.csv', # fix demo product.template & product.product. hr.employee.product_id using product.product
    ],
}