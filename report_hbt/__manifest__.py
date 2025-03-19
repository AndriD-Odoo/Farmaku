# -*- coding: utf-8 -*-
{
    "name": "Report HBT",
    "summary": """
        Last purchase per item per vendor
    """,
    "description": """
        
    """,
    "author": "Odoo Freelancer",
    "website": "",
    "category": "Purchase",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "purchase",
        "stock",
        "purchase_stock",
        "asb_base_farmaku",
        "purchase_discount",
        "purchase_extended",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/report_hbt_wizard_views.xml",
        "views/report_hbt_views.xml",
    ],
    "demo": [

    ],
}
