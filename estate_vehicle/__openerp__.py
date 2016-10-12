# -*- coding: utf-8 -*-
{
    'name': "Estate Vehicle",

    'summary': """
        Estate Management Additional for Vehicle""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Mahroza And Probo :)",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','fleet','estate_nursery'],
    # ,'hr','estate',

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'templates.xml',
        'wizard/reject.xml',
        'views/estate_vehicle_fuel_log.xml',
        'views/estate_vehicle_otherservice_log.xml',
        'views/estate_vehicle_sparepart_log.xml',
        'views/inherit_vehicle_log_oil.xml',
        # 'views/inherit_transfertomn_spb_view',
        'views/timesheet_sequence.xml',
        'views/estate_vehicle_timesheet.xml',
        'views/estate_nursery_vehicle.xml',
        'views/estate_vehicle_path.xml',
        'views/estate_vehicle_master_factor.xml',
        'views/estate_vehicle_master_formula.xml',
        'views/estate_vehicle_master_categoryunit.xml',
        'views/view_timesheet_premi.xml',
        'views/view_summary_cost_vehicle.xml',
        'views/inherit_transfertomn_spb_view.xml',
        'views/fleet_vehicle_timesheet.xml',
        'workflow/workflow_fleet_vehicle_timesheet.xml'


        # 'views/inherit_activity_typebreakdown.xml',



    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
        'demo/master_factor.xml',
        'demo/estate.activity.csv',
        'demo/path.location.csv',
        'demo/master_category_unit.xml',
        'demo/hr_job.xml',
        'demo/master_formula_activity_vehicle.xml',
        'demo/fleet.vehicle.model.brand.csv',
        'demo/fleet.vehicle.model.csv',

    ],
}