# -*- coding: utf-8 -*-
{
    "name": "Purchase Extended",
    "summary": """
        Extend function of purchase order module
    """,
    "description": """
        
    """,
    "author": "Odoo Freelancer",
    "website": "",
    "category": "Purchase",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "product",
        "stock",
        "stock_account",
        "purchase",
        "base_extended",
        "purchase_stock",
        "mail_extended",
        "purchase_discount",
    ],
    "data": [
        "data/mail_template_data.xml",
        "data/ir_cron.xml",
        "views/menu.xml",
        "views/stock_picking_views.xml",
        "views/product_supplierinfo_views.xml",
        "views/purchase_order_views.xml",
        "views/res_partner_views.xml",
        "views/stock_move_line_views.xml",
        "report/purchase_order_templates.xml",
        "report/purchase_quotation_templates.xml",
        "report/new_purchase_order_templates.xml",
    ],
    "demo": [

    ],
}
