# -*- coding: utf-8 -*-
{
    'name': "Estate Nursery",

    'summary': """
        Manage Nursery.""",

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
    'depends': ['base','estate','stock','product','report','board','purchase','membership','mrp'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'templates.xml',
        'views/estate_nursery_view.xml',
        'views/estate_nursery_selection_view.xml',
        'views/estate_nursery_culling.xml',
        'views/estate_planting_view.xml',
        'views/estate_nursery_cleaving_seed_view.xml',
        'views/report_plantation_view.xml',
        'views/dashboard_selection.xml',
        'reports/selection_report.xml',
        'reports/batch_report.xml',
        'reports/requestplanting_report.xml',
        'reports/reportplantation_prenursery_report.xml',
        'reports/reportplantation_prenursery_div.xml',
        'reports/reportplantation_mainnursery_report.xml',
        'reports/reportplantation_seedreceived.xml',
        'reports/reportplantation_seedreceived_bag.xml',
        'reports/reportplantation_culling.xml',
        'reports/reportplantation_cullingbatch.xml',
        'workflow/session_selection_workflow.xml',
        'workflow/session_cleaving_workflow.xml',
        'workflow/session_workflow.xml',
        'workflow/session_culling_workflow.xml',
        'workflow/session_requestplanting_workflow.xml',
        'workflow/session_planting_workflow.xml',
        'res_config_view.xml',
        'selection_report.xml',
        'batch_report.xml',
        'report_culling.xml',
        'report_culling_batch.xml',
        'reportplantation_prenursery_report.xml',
        'reportplantation_bpb.xml',
        'reportplantation_div.xml',
        'reportmainnursery_div.xml',
        'reportplantation_seedreceived.xml',
        'reportplantation_seedreceived_bag.xml',
        'views/sequence_view.xml',
        # 'wizard/req_wiz.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}