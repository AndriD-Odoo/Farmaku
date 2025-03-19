# -*- coding: utf-8 -*-
{
    "name": "Inter Company Module for Sale/Purchase Orders and Invoices Extended",
    "summary": """
        Extend function of sale_purchase_inter_company_rules module
    """,
    "description": """
        
    """,
    "author": "Odoo Freelancer",
    "website": "",
    "category": "Productivity",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "stock",
        "sale_purchase_inter_company_rules",
        "purchase_discount",
        "purchase_conversion_uom",
    ],
    "data": [
        "data/ir_config_parameter.xml",
        "views/purchase_order_views.xml",
        "views/sale_order_views.xml",
        "views/stock_warehouse_views.xml",
    ],
    "demo": [

    ],
}
