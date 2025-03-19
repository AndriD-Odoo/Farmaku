# -*- coding: utf-8 -*-
{
    "name": "Purchase Return Type",
    "summary": """
        Return type of purchase order
    """,
    "description": """
        
    """,
    "author": "Odoo Freelancer",
    "website": "",
    "category": "Purchases",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "product",
        "stock",
        "purchase",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/purchase_return_type_views.xml",
        "views/stock_picking_views.xml",
        "views/res_partner_views.xml",
    ],
    "demo": [

    ],
}
