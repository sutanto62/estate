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
        'views/estate_master_catalog.xml',
        'views/estate_mecanic_timesheet.xml',
        'views/estate_master_workshop_shedule.xml',
        'views/estate_master_mapping_asset.xml',
        'views/inherit_equipment.xml',
        'views/estate_service_external.xml',
        'views/estate_workshop_cost.xml',
        'views/inherit_hr_contract.xml',
        'views/view_cost_workshop.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
        'demo/estate.activity.csv',
        'demo/estate_workshop_code.xml',

    ],
}