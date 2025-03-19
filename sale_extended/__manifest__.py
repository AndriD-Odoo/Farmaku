# -*- coding: utf-8 -*-
{
    "name": "Sale Extended",
    "summary": """
        Extend function of sales module
    """,
    "description": """

    """,
    "author": "Odoo Freelancer",
    "website": "",
    "category": "Sales",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "sale",
        "sale_management",
        "pos_sale",
        "account_extended",
        "asb_base_farmaku",
        "sale_enterprise",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/res_partner_views.xml",
        "views/stock_warehouse_views.xml",
        "views/sale_order_views.xml",
        "views/crm_team_views.xml",
        "views/rafaksi_views.xml",
        "views/account_move_views.xml",
        "wizard/rafaksi_wizard_views.xml",
        "report/sale_report.xml",
        "report/report_invoice.xml",
        "report/commercial_invoice.xml",
    ],
    "demo": [

    ],
}
