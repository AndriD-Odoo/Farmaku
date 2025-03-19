# -*- coding: utf-8 -*-
{
    "name": "Purchase Report",
    "summary": """
        Report tracking PO, report perubahan harga PO
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
        "purchase_extended",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/purchase_report_farmaku_views.xml",
        "wizard/purchase_report_wizard_views.xml",
    ],
    "demo": [

    ],
}
