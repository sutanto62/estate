# -*- coding: utf-8 -*-
{
    'name': "Budget Estate Extension",

    'summary': """
        Add estate budgeting functional, estate budgeting consist of labour, material, other.
        """,

    'description': """
        Differentiate budgeting into for types of calculation, now budgeting can calculate total workday, total amount of labour, material and other.
    """,

    'author': "Palmagroup",
    'website': "http://www.palmagroup.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account_budget'],

    # always loaded
    'data': [
        'views/budget_estate.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}