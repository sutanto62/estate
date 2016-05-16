# -*- coding: utf-8 -*-
{
    'name': "Estate Vehicle",

    'summary': """
        Estate Management Additional for Vehicle""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Mahroza",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','fleet','hr'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/estate_nursery_vehicle.xml',
        'views/estate_vehicle_path.xml',
        'views/estate_vehicle_master_factor.xml',
        'views/estate_vehicle_timesheet.xml',
        'views/estate_vehicle_fuel_log.xml',
        'views/inherit_vehicle_log_oil.xml',
        'views/inherit_vehicle_log_fuel.xml',
        'views/estate_vehicle_otherservice_log.xml',
        'views/estate_vehicle_sparepart_log.xml'
        # 'views/timesheet_sequence.xml',
        #'workflow/workflow_estate_timesheet_activity_transport.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}