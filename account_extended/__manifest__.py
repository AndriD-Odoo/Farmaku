# -*- coding: utf-8 -*-
{
    "name": "Account Extended",
    "summary": """
        Extend function of accounting and finance module
    """,
    "description": """

    """,
    "author": "Odoo Freelancer",
    "website": "",
    "category": "Accounting",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "account",
        "base_extended",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "views/electronic_data_capture_views.xml",
        "views/payment_method_views.xml",
        "report/report_invoice.xml",
        "report/commercial_invoice.xml",
    ],
    "demo": [

    ],
}
