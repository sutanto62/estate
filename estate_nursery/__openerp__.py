# -*- coding: utf-8 -*-
{
    'name': "Estate Nursery",

    'summary': """
        Manage Nursery.""",

    'description': """
        This module for selection nursery,transfer to MN , Transplanting to PN, and
        include :
        - Purhcasing  seed
        - Transfer seed
        - Selection Batch receiving
        - Selection PN and MN
        - Transfer Seed To MN
        - Transplanting
            - Create Seed Request order
            - Create Seed Delivery order
        - Culling Seed

    """,

    'author': "Mahroza And Probo",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['estate','base',
                'purchase',
                'report','board',
                'web_readonly_bypass','mail'],
    # estate_vehicle'
    # always loaded
    'data': [
        'demo/partner_data.xml',
        'security/ir.model.access.csv',

        'config_reports/selection_report.xml',
        'config_reports/batch_report.xml',
        'config_reports/report_cleaving.xml',
        'config_reports/report_culling.xml',
        'config_reports/report_culling_batch.xml',
        'config_reports/reportplantation_prenursery_report.xml',
        'config_reports/reportplantation_bpb.xml',
        'config_reports/reportplantation_div.xml',
        'config_reports/reportmainnursery_div.xml',
        'config_reports/reportplantation_seedreceived.xml',
        'config_reports/reportplantation_seed_do.xml',

        'templates.xml',
        'views/inherit_blocktemplate.xml',
        'views/estate_nursery_transfermn.xml',
        'views/estate_nursery_view.xml',
        'views/estate_nursery_selection_view.xml',
        'views/estate_nursery_culling.xml',
        'views/estate_nursery_cleaving_seed_view.xml',
        'views/estate_nursery_recovery.xml',
        'views/report_plantation_view.xml',
        'views/sequence_view_planting.xml',
        'views/estate_planting_view.xml',
        'views/dashboard_selection.xml',


        'reports/selection_report.xml',
        'reports/batch_report.xml',
        'reports/requestplanting_report.xml',
        'reports/reportplantation_prenursery_report.xml',
        'reports/reportplantation_prenursery_div.xml',
        'reports/reportplantation_mainnursery_report.xml',
        'reports/reportplantation_seedreceived.xml',
        'reports/reportplantation_culling.xml',
        'reports/reportplantation_cullingbatch.xml',
        'reports/reportplantation_cleaving.xml',
        'reports/reportplantation_seeddo.xml',

        'workflow/session_selection_workflow.xml',
        'workflow/session_cleaving_workflow.xml',
        'workflow/session_workflow.xml',
        'workflow/session_culling_workflow.xml',
        'workflow/session_requestplanting_workflow.xml',
        'workflow/session_planting_workflow.xml',
        'workflow/session_recovery_workflow.xml',
        'workflow/session_transfertomn_workflow.xml',
        'workflow/session_returnseed_workflow.xml',
        'res_config_view.xml',


        'views/sequence_view.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
        'demo/partner_demo.xml'
    ],
}