# -*- coding: utf-8 -*-
{
    "name": "Product Expiry Extended",
    "summary": """
        Extend function of product expiry module, report near expired date
    """,
    "description": """
        
    """,
    "author": "Odoo Freelancer",
    "website": "",
    "category": "Inventory",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "product",
        "stock",
        "purchase",
        "base_extended",
        "purchase_stock",
        "product_expiry",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_move_views.xml",
        "views/stock_quant_views.xml",
        "views/stock_production_lot_views.xml",
        "wizard/near_expired_date_wizard.xml",
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
    ],
    "demo": [

    ],
}
