# -*- coding: utf-8 -*-
{
    'name': "Purchase Indonesia",

    'summary': """
       """,

    'description': """
        Module For Purchase , Procurement , And Inventory Indonesia
    """,

    'author': "Mahroza And Probo",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','base_indonesia','purchase_request','purchase_requisition','estate','account_budget'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/reject.xml',
        # 'wizard/Inherit_purchase_indonesia_requisition_partner.xml',
        'config_report/config_quotation_comparison_form.xml',
        'config_report/config_goods_receipt_notes.xml',
        'config_report/config_purchase_order.xml',
        'config_report/config_purchase_quotation.xml',
        'config_report/config_purchase_request.xml',

        'views/inherit_purchase_request.xml',
        'views/procur_request_sequence.xml',
        'views/procur_request_view.xml',
        'views/management_good_request.xml',
        'views/inherit_purchaseorder_report.xml',
        'views/inherit_purchase_order.xml',
        'views/inherit_stock_picking.xml',
        'views/purchase_setting.xml',
        'views/quotation_comparison.xml',
        'views/inherit_purchase_tender.xml',
        'views/procurement_process.xml',
        'views/procur_return_view.xml',
        'workflow/workflow_procur_good_request.xml',
        'workflow/workflow_management_good_request.xml',
        # 'workflow/workflow_quotation_comparison_form.xml',

        'reports/report_quotation_comparison_form.xml',
        'reports/report_goods_receipt_notes.xml',
        'reports/report_purchase_order.xml',
        'reports/report_purchase_quotation.xml',
        'reports/report_purchase_request.xml'


        # 'templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
    'qweb': [
        'static/src/xml/purchase_requisition.xml',
    ],
}
