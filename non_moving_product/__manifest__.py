# -*- coding: utf-8 -*-
{
    "name": "Non Moving Product Report",
    "summary": """
        Products that have not been sold for x days since the last purchase
    """,
    "description": """

    """,
    "author": "Odoo Freelancer",
    "website": "",
    "category": "Purchasing",
    "version": "14.0.1.0.0",
    "depends": [
        "purchase",
        "sale",
        "stock",
        "purchase_stock",
        "sale_stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/non_moving_product_wizard.xml",
    ],
    "demo": [

    ],
}
